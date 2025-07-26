#!/usr/bin/env python3
"""
Marstek PV-Akku Steuerung - Hauptanwendung v3.4
Schlanke, robuste Implementierung mit Web-Integration für Regelungslogs
"""

import sys
import time
import logging
import threading
import signal
from pathlib import Path
from datetime import datetime

# Lokale Module
from config_loader import ConfigLoader
from shelly_client import ShellyClient
from ecotracker_client import EcoTrackerClient
from battery_client import BatteryManager
from zero_feed_control import ZeroFeedController
from web_server import SimpleWebServer

# Logging-Setup
def setup_logging(config: ConfigLoader):
    """Konfiguriert Logging basierend auf Konfiguration"""
    log_config = config.get_logging_config()
    
    # Log-Level
    level = getattr(logging, log_config.get('level', 'INFO').upper(), logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    log_file = log_config.get('file')
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=log_config.get('max_file_size_mb', 10) * 1024 * 1024,
                backupCount=log_config.get('backup_count', 3)
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            logging.info(f"Log-Datei konfiguriert: {log_path}")
        except Exception as e:
            logging.warning(f"Log-Datei konnte nicht konfiguriert werden: {e}")
    
    # Externe Bibliotheken leiser stellen
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

class MartekSystem:
    """Hauptklasse für das Marstek PV-Akku Steuerungssystem"""
    
    def __init__(self):
        self.config = None
        self.energy_meter = None  # Kann Shelly oder EcoTracker sein
        self.batteries = None
        self.controller = None
        self.web_server = None
        self.web_thread = None
        
        self.running = False
        self.meter_failure_count = 0
        self.max_meter_failures = 2
        self.last_soc_update = 0
        
        # Graceful Shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Signal-Handler für graceful shutdown"""
        self.logger.info(f"Signal {signum} empfangen - beende System...")
        self.running = False
    
    def initialize(self) -> bool:
        """Initialisiert alle Systemkomponenten"""
        try:
            self.logger.info("=== Marstek PV-Akku Steuerung v3.4 ===")
            self.logger.info("Initialisiere System...")
            
            # 1. Konfiguration laden
            self.config = ConfigLoader()
            self.config.load()
            self.logger.info("✓ Konfiguration geladen")
            
            # 2. Energy Meter Client erstellen (Shelly oder EcoTracker)
            meter_type = self.config.get_energy_meter_type()
            meter_config = self.config.get_energy_meter_config()
            
            if meter_type == 'shelly':
                self.energy_meter = ShellyClient(
                    ip=meter_config['ip'],
                    timeout=meter_config.get('timeout_seconds', 5)
                )
                self.logger.info(f"✓ Shelly als Energy Meter konfiguriert")
            elif meter_type == 'ecotracker':
                self.energy_meter = EcoTrackerClient(
                    ip=meter_config['ip'],
                    timeout=meter_config.get('timeout_seconds', 5)
                )
                self.logger.info(f"✓ EcoTracker als Energy Meter konfiguriert")
            
            # Energy Meter Verbindung testen
            if not self.energy_meter.is_online():
                self.logger.warning(f"⚠️ {meter_type} nicht erreichbar - System startet trotzdem")
            else:
                self.logger.info(f"✓ {meter_type}-Verbindung OK")
                
            self.max_meter_failures = meter_config.get('max_failures_before_stop', 2)
            
            # 3. Battery-Manager erstellen
            battery_config = self.config.get_battery_config()
            self.batteries = BatteryManager(
                ip=battery_config['ip'],
                port=battery_config['port'],
                akku_ids=battery_config['akku_ids'],
                timeout=battery_config.get('timeout_seconds', 3)
            )
            self.logger.info("✓ Battery-Manager erstellt")
            
            # 4. Web-Server ZUERST erstellen (ohne Controller)
            self.web_server = SimpleWebServer(
                shelly_client=self.energy_meter,  # Funktioniert für beide Meter-Typen
                battery_manager=self.batteries,
                controller=None,  # Wird später gesetzt
                config=self.config
            )
            self.logger.info("✓ Web-Server erstellt")
            
            # 5. Controller MIT Web-Server Referenz erstellen
            self.controller = ZeroFeedController(
                shelly_client=self.energy_meter,  # Funktioniert für beide Meter-Typen
                battery_manager=self.batteries,
                config=self.config,
                web_server=self.web_server  # NEU: Web-Server übergeben
            )
            
            # 6. Controller im Web-Server setzen
            self.web_server.controller = self.controller
            self.logger.info("✓ Zero-Feed-Controller erstellt und verknüpft")
            
            self.logger.info("=== System erfolgreich initialisiert ===")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialisierung fehlgeschlagen: {e}")
            return False
    
    def start_web_server(self):
        """Startet Web-Server in separatem Thread"""
        try:
            web_config = self.config.get_web_config()
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 8080)
            
            self.web_thread = threading.Thread(
                target=self.web_server.run,
                kwargs={'host': host, 'port': port, 'debug': False},
                daemon=True
            )
            self.web_thread.start()
            
            self.logger.info(f"🌐 Web-Server gestartet: http://{host}:{port}")
            
            # Kurz warten und Browser öffnen
            time.sleep(2)
            try:
                import webbrowser
                browser_url = f"http://localhost:{port}" if host == '0.0.0.0' else f"http://{host}:{port}"
                webbrowser.open(browser_url)
                self.logger.info(f"🌐 Browser geöffnet: {browser_url}")
            except Exception:
                pass  # Browser-Öffnung ist optional
                
        except Exception as e:
            self.logger.error(f"❌ Web-Server-Start fehlgeschlagen: {e}")
    
    def run_main_loop(self):
        """Hauptsteuerungsschleife"""
        self.logger.info("🎯 Starte Hauptsteuerungsschleife")
        
        control_config = self.config.get_control_config()
        control_interval = control_config.get('poll_interval_seconds', 2)  # Steuerung alle 2s
        meter_poll_interval = 1  # Energy Meter alle 1s abrufen
        soc_interval = control_config.get('soc_update_interval_seconds', 30)
        meter_type = self.config.get_energy_meter_type()
        
        self.logger.info(f"Optimierte Intervalle: {meter_type}-Poll={meter_poll_interval}s, Steuerung={control_interval}s, SoC={soc_interval}s")
        self.logger.info(f"Durchschnittsbildung: Letzten 3 {meter_type}-Abrufe für Regelung verwenden")
        
        last_control = 0
        last_soc_update = 0
        last_meter_poll = 0
        iteration = 0
        
        self.running = True
        
        while self.running:
            try:
                current_time = time.time()
                iteration += 1
                
                # 1. Energy Meter alle 1s abrufen für Durchschnittsbildung
                if current_time - last_meter_poll >= meter_poll_interval:
                    current_power = self.energy_meter.poll_current_power()
                    if current_power is not None:
                        # Erfolgreicher Abruf - Fehlerzähler zurücksetzen
                        if self.meter_failure_count > 0:
                            self.logger.info(f"✓ {meter_type} wieder erreichbar (war {self.meter_failure_count} Fehler)")
                            self.meter_failure_count = 0
                            self.web_server.add_log_entry('info', f"{meter_type}-Verbindung wiederhergestellt")
                    else:
                        # Fehler beim Abruf
                        self.meter_failure_count += 1
                        if self.meter_failure_count == self.max_meter_failures:
                            self.logger.error(f"🚨 {meter_type} {self.max_meter_failures}x nicht erreichbar - stoppe alle Akkus!")
                            self.batteries.stop_all()
                            self.web_server.add_log_entry('error', f"{meter_type}-Ausfall - Akkus gestoppt")
                    
                    last_meter_poll = current_time
                
                # 2. Steuerungszyklus alle 2s (basierend auf Durchschnitt)
                if current_time - last_control >= control_interval:
                    if self.meter_failure_count < self.max_meter_failures:
                        success, status = self.controller.execute_control_cycle()
                        
                        if success:
                            # Kompakte Ausgabe mit Durchschnittswerten
                            if iteration % (control_interval * 5) == 1:  # Alle 10s loggen
                                avg_power = self.energy_meter.get_power()
                                current_direct = self.energy_meter.get_current_power_direct() 
                                battery_power = self.batteries.get_total_power()
                                history_len = len(self.energy_meter.power_history)
                                self.logger.info(
                                    f"Grid: {avg_power or 0:>6.0f}W (Ø{history_len}) | "
                                    f"Aktuell: {current_direct or 0:>6.0f}W | "
                                    f"Akku: {battery_power:>6.0f}W | {status}"
                                )
                        else:
                            self.logger.warning(f"Steuerung fehlgeschlagen: {status}")
                            self.web_server.add_log_entry('warning', f"Steuerung: {status}")
                    else:
                        # Energy Meter-Ausfall: Akkus gestoppt
                        if iteration % (60 // control_interval) == 1:  # Alle 60s loggen bei Ausfall
                            self.logger.error(f"🚨 {meter_type}-Ausfall: Akkus gestoppt!")
                            self.web_server.add_log_entry('error', f"{meter_type}-Ausfall: Akkus gestoppt")
                    
                    last_control = current_time
                
                # 3. SoC-Updates
                if current_time - last_soc_update >= soc_interval:
                    self._update_battery_soc()
                    last_soc_update = current_time
                
                # 4. Kurz warten
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Benutzerunterbrechung erkannt")
                break
            except Exception as e:
                self.logger.error(f"Fehler in Hauptschleife: {e}")
                time.sleep(5)
        
        self.logger.info("Hauptschleife beendet")
    
    def _update_battery_soc(self):
        """Aktualisiert SoC aller Akkus"""
        try:
            soc_values = self.batteries.update_all_soc()
            
            # **NUR für Web-Interface loggen, NICHT auf Konsole**
            soc_parts = []
            for akku_id, soc in soc_values.items():
                if soc is not None:
                    soc_parts.append(f"Akku {akku_id}: {soc:.0f}%")
                else:
                    soc_parts.append(f"Akku {akku_id}: --")
            
            if soc_parts:
                soc_msg = " | ".join(soc_parts)
                # **KEIN Logger.info mehr! Nur Web-Interface**
                # Konsolen-Log entfernt - nur noch Web-Interface
                self.web_server.add_log_entry('info', f"🔋 SoC: {soc_msg}")
            
        except Exception as e:
            # Fehler weiterhin loggen
            self.logger.warning(f"SoC-Update fehlgeschlagen: {e}")
            self.web_server.add_log_entry('warning', f"SoC-Update: {e}")
    
    def shutdown(self):
        """Fährt System sauber herunter"""
        self.logger.info("🛑 Starte System-Shutdown...")
        
        try:
            # Akkus stoppen
            if self.batteries:
                self.batteries.stop_all()
                self.logger.info("✓ Akkus gestoppt")
            
            # Web-Server wird automatisch beendet (daemon thread)
            
            self.logger.info("✓ System sauber heruntergefahren")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Shutdown: {e}")
    
    def run(self) -> bool:
        """Hauptmethode - führt kompletten System-Lebenszyklus aus"""
        try:
            # Initialisierung
            if not self.initialize():
                return False
            
            # Web-Server starten
            self.start_web_server()
            
            # Hauptschleife starten
            self.run_main_loop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Kritischer Systemfehler: {e}")
            return False
        finally:
            self.shutdown()

def main():
    """Hauptfunktion"""
    try:
        # Konfiguration für Logging laden
        config = ConfigLoader()
        config.load()
        setup_logging(config)
        
        # System erstellen und starten
        system = MartekSystem()
        success = system.run()
        
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"❌ Konfigurationsfehler: {e}")
        print("Erstelle eine 'config.json' Datei mit den erforderlichen Einstellungen.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()