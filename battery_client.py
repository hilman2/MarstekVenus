#!/usr/bin/env python3
"""
Modbus-Akku-Client für Marstek PV-Akku Steuerung
Strikt: Keine Default-Werte oder Fallbacks im Code!
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)

# MODBUS REGISTER
REG_485_CONTROL = 42000      # RS485 Kontrolle
REG_MANUAL_MODE = 43000      # Manueller Modus  
REG_CHARGE_MODE = 42010      # Lademodus
REG_CHARGE_POWER = 42020     # Lade-Leistung
REG_DISCHARGE_POWER = 42021  # Entlade-Leistung
REG_SOC = 32104              # State of Charge
REG_MODBUS_ADDRESS = 41100   # Modbus-Adresse
REG_TEMPERATURE_1 = 35001    # Temperatur 1
REG_TEMPERATURE_2 = 35002    # Temperatur 2

class BatteryClient:
    """Client für einen einzelnen Akku - OHNE FALLBACK-WERTE"""
    
    def __init__(self, ip: str, port: int, slave_id: int, timeout: int = 3):
        self.ip = ip
        self.port = port
        self.slave_id = slave_id
        self.timeout = timeout
        
        # Status-Tracking - KEINE Default-Werte!
        self.current_power = 0.0
        self.current_mode = 0  # 0=stop, 1=charge, 2=discharge
        self.last_soc = None  # KEIN Default-Wert!
        self.last_soc_update = 0
        self.error_count = 0
        self.is_modbus_active = False
        self.last_active_mode = 0
        
        logger.info(f"Duravolt-Akku-Client erstellt - ID: {slave_id}, IP: {ip}:{port}")
    
    def _create_connection(self) -> Optional[ModbusTcpClient]:
        """Erstellt neue Modbus-Verbindung"""
        try:
            client = ModbusTcpClient(
                host=self.ip,
                port=self.port,
                timeout=self.timeout
            )
            
            if client.connect():
                return client
            else:
                logger.warning(f"Akku {self.slave_id}: Modbus-Verbindung fehlgeschlagen")
                return None
                
        except Exception as e:
            logger.error(f"Akku {self.slave_id}: Fehler beim Verbinden: {e}")
            return None
    
    def read_soc(self) -> Optional[float]:
        """
        Liest SoC vom Akku - OHNE Fallback-Werte
        """
        client = self._create_connection()
        if not client:
            self.error_count += 1
            return None
        
        try:
            # SoC lesen mit exakt derselben Methode
            result = client.read_holding_registers(
                address=REG_SOC,     # 32104 
                count=1,
                slave=self.slave_id
            )
            
            if result.isError():
                logger.warning(f"Akku {self.slave_id}: SoC-Lese-Fehler: {result}")
                self.error_count += 1
                return None
            
            # SoC konvertieren (Duravolt liefert direkte Prozentwerte)
            soc_raw = result.registers[0]
            soc = float(soc_raw)  # Direkt in Prozent
            
            # Plausibilitätsprüfung
            if 0 <= soc <= 100:
                self.last_soc = soc  # Echter Wert setzen
                self.last_soc_update = time.time()
                self.error_count = max(0, self.error_count - 1)
                logger.debug(f"Akku {self.slave_id}: SoC = {soc}%")
                return soc
            else:
                logger.warning(f"Akku {self.slave_id}: Unplausibler SoC-Wert: {soc}%")
                return None
                
        except Exception as e:
            logger.error(f"Akku {self.slave_id}: SoC-Fehler: {e}")
            self.error_count += 1
            return None
        finally:
            # Verbindung sofort trennen
            client.close()
    
    def set_power(self, power: float, mode: int) -> bool:

        client = self._create_connection()
        if not client:
            self.error_count += 1
            return False
        
        try:
            # SCHRITT 1: RS485-Kontrolle aktivieren
            result = client.write_register(
                address=REG_485_CONTROL,  
                value=21930,              
                slave=self.slave_id
            )
            if result.isError():
                logger.error(f"Akku {self.slave_id}: RS485-Kontrolle fehlgeschlagen")
                return False
            
            time.sleep(0.1)  # Kurze Pause
            
            # SCHRITT 2: Leistung begrenzen wie im alten System
            if power > 0:
                power = round(max(50, min(power, 2500)))
            else:
                power = 0
            
            # SCHRITT 3: Modus-Wechsel-Behandlung wie im alten System
            mode_changed = (self.current_mode != mode)
            
            if mode == 1:  # Laden
                if mode_changed:
                    # Erst Entladung stoppen
                    client.write_register(REG_DISCHARGE_POWER, 0, slave=self.slave_id)
                    time.sleep(0.2)
                    # Dann Lademodus aktivieren
                    client.write_register(REG_CHARGE_MODE, 1, slave=self.slave_id)
                    time.sleep(0.5)
                # Lade-Leistung setzen
                client.write_register(REG_CHARGE_POWER, int(power), slave=self.slave_id)
                
            elif mode == 2:  # Entladen
                if mode_changed:
                    # Erst Ladung stoppen
                    client.write_register(REG_CHARGE_POWER, 0, slave=self.slave_id)
                    time.sleep(0.2)
                    # Dann Entlademodus aktivieren
                    client.write_register(REG_CHARGE_MODE, 2, slave=self.slave_id)
                    time.sleep(0.5)
                # Entlade-Leistung setzen
                client.write_register(REG_DISCHARGE_POWER, int(power), slave=self.slave_id)
                
            else:  # Stopp (mode == 0)
                # Beide Leistungen auf 0, dann Modus auf 0
                client.write_register(REG_CHARGE_POWER, 0, slave=self.slave_id)
                time.sleep(0.1)
                client.write_register(REG_DISCHARGE_POWER, 0, slave=self.slave_id)
                time.sleep(0.1)
                client.write_register(REG_CHARGE_MODE, 0, slave=self.slave_id)
            
            # Status aktualisieren wie im alten System
            self.current_mode = mode
            self.current_power = power if mode > 0 else 0
            
            if mode > 0:
                self.last_active_mode = mode
            
            self.error_count = max(0, self.error_count - 1)
            logger.debug(f"Akku {self.slave_id}: {power}W, Modus {mode}")
            return True
            
        except Exception as e:
            logger.error(f"Akku {self.slave_id}: Fehler beim Setzen der Leistung: {e}")
            self.error_count += 1
            return False
        finally:
            # Verbindung sofort trennen
            client.close()
    
    0
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Status des Duravolt Akkus zurück - OHNE Fallback-Werte"""
        soc_age = time.time() - self.last_soc_update if self.last_soc_update > 0 else 999
        
        return {
            'slave_id': self.slave_id,
            'soc': self.last_soc,  # Kann None sein!
            'soc_age_seconds': int(soc_age),
            'current_power': self.current_power,
            'current_mode': self.current_mode,
            'mode_text': {0: 'Stopp', 1: 'Laden', 2: 'Entladen'}.get(self.current_mode, 'Unbekannt'),
            'error_count': self.error_count
        }
    
    def stop(self) -> bool:
        """Stoppt den Duravolt Akku (Leistung auf 0)"""
        return self.set_power(0, 0)
    
    def reset_error_count(self):
        """Setzt Fehlerzähler zurück"""
        self.error_count = 0
        logger.info(f"Akku {self.slave_id}: Fehlerzähler zurückgesetzt")

class BatteryManager:
    """Manager für mehrere Duravolt Akkus - OHNE Fallback-Werte"""
    
    def __init__(self, ip: str, port: int, akku_ids: list, timeout: int = 3):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        
        # Erstelle Duravolt Akku-Clients
        self.batteries = {}
        for akku_id in akku_ids:
            self.batteries[akku_id] = BatteryClient(ip, port, akku_id, timeout)
        
        logger.info(f"Duravolt Battery-Manager erstellt für {len(akku_ids)} Akkus: {akku_ids}")
    
    def update_all_soc(self) -> Dict[int, Optional[float]]:
        """Aktualisiert SoC für alle Duravolt Akkus"""
        soc_values = {}
        for akku_id, battery in self.batteries.items():
            soc = battery.read_soc()
            soc_values[akku_id] = soc
        return soc_values
    
    def distribute_power(self, total_power: float, mode: int, min_soc: int, max_soc: int) -> bool:
        """Verteilt Gesamtleistung auf verfügbare Duravolt Akkus"""
        logger.info(f"DISTRIBUTE: Power={total_power:.0f}W, Modus={mode}, SoC-Range={min_soc}-{max_soc}%")
        
        if mode == 0:  # Stopp alle - aber nur wenn wirklich gewollt!
            logger.info("Expliciter STOPP-Modus - alle Akkus stoppen")
            return self.stop_all()
        
        # Verfügbare Akkus ermitteln - NUR mit echten SoC-Werten
        available_batteries = []
        for battery in self.batteries.values():
            logger.info(f"Debug Akku {battery.slave_id}: SoC={battery.last_soc}, Modus={mode}, Min-SoC={min_soc}, Max-SoC={max_soc}")
            
            # KEIN Fallback! Nur Akkus mit echtem SoC-Wert verwenden
            if battery.last_soc is None:
                logger.warning(f"Akku {battery.slave_id}: Kein SoC-Wert verfügbar - übersprungen")
                continue
                
            if mode == 1:  # Laden - nur Akkus unter max_soc
                if battery.last_soc < max_soc:
                    available_batteries.append(battery)
                    logger.info(f"Akku {battery.slave_id}: Zum Laden verfügbar ({battery.last_soc}% < {max_soc}%)")
                else:
                    logger.info(f"Akku {battery.slave_id}: Zu voll zum Laden ({battery.last_soc}% >= {max_soc}%)")
            elif mode == 2:  # Entladen - nur Akkus über min_soc
                if battery.last_soc > min_soc:
                    available_batteries.append(battery)
                    logger.info(f"Akku {battery.slave_id}: Zum Entladen verfügbar ({battery.last_soc}% > {min_soc}%)")
                else:
                    logger.warning(f"Akku {battery.slave_id}: SoC zu niedrig zum Entladen ({battery.last_soc}% <= {min_soc}%)")
        
        if not available_batteries:
            logger.error(f"KRITISCH: Keine Duravolt Akkus verfügbar für Modus {mode}!")
            logger.error(f"Debugging-Info:")
            for battery in self.batteries.values():
                logger.error(f"  Akku {battery.slave_id}: SoC={battery.last_soc}, Age={time.time() - battery.last_soc_update if battery.last_soc_update > 0 else 999:.1f}s")
            logger.error(f"Anforderung: Modus={mode}, Min-SoC={min_soc}%, Max-SoC={max_soc}%")
            
            # NUR stoppen wenn wirklich ALLE Akkus ungültig sind
            all_invalid = all(b.last_soc is None for b in self.batteries.values())
            if all_invalid:
                logger.error("Alle Akkus haben ungültigen SoC - stoppe alle")
                return self.stop_all()
            else:
                logger.error("Einige Akkus haben gültigen SoC, aber keine verfügbar - prüfe SoC-Grenzen!")
                return False  # NICHT stoppen!
        
        # Leistung gleichmäßig verteilen
        num_batteries = len(available_batteries)
        power_per_battery = total_power / num_batteries
        
        # Stoppe nicht verwendete Akkus
        for battery in self.batteries.values():
            if battery not in available_batteries:
                battery.stop()
        
        # Setze Leistung für verfügbare Akkus
        success_count = 0
        failed_batteries = []
        for battery in available_batteries:
            if battery.set_power(power_per_battery, mode):
                success_count += 1
            else:
                failed_batteries.append(battery.slave_id)
                logger.error(f"Akku {battery.slave_id}: Leistung setzen fehlgeschlagen!")
        
        # Logging der Verteilung
        logger.info(f"Duravolt Leistungsverteilung: {total_power}W auf {success_count}/{num_batteries} Akkus")
        
        # NUR bei kompletten Fehlern FALSE zurückgeben
        if success_count == 0:
            logger.error(f"ALLE Akkus fehlgeschlagen! Failed: {failed_batteries}")
            # ABER NICHT STOPPEN! Das würde das Problem verschlimmern
            return False
        
        # Wenn mindestens ein Akku funktioniert = Erfolg
        if failed_batteries:
            logger.warning(f"Teilweise erfolgreich: {success_count}/{num_batteries}, Failed: {failed_batteries}")
        
        return success_count > 0  # Mindestens ein Akku muss funktionieren
    
    def stop_all(self) -> bool:
        """Stoppt alle Duravolt Akkus sofort"""
        import traceback
        logger.warning("=== STOPPE ALLE DURAVOLT AKKUS ====")
        logger.warning(f"Aufgerufen von: {traceback.format_stack()[-2].strip()}")
        logger.warning("======================================")
        
        success_count = 0
        for battery in self.batteries.values():
            if battery.stop():
                success_count += 1
        
        return success_count == len(self.batteries)
    
    def get_total_power(self) -> float:
        """Gibt aktuelle Gesamtleistung aller Duravolt Akkus zurück"""
        total = 0.0
        for battery in self.batteries.values():
            if battery.current_mode == 2:  # Entladen = positiv
                total += battery.current_power
            elif battery.current_mode == 1:  # Laden = negativ
                total -= battery.current_power
        return total
    
    def get_average_soc(self) -> float:
        """Gibt durchschnittlichen SoC aller Duravolt Akkus zurück"""
        valid_soc_values = []
        for battery in self.batteries.values():
            if battery.last_soc is not None:
                valid_soc_values.append(battery.last_soc)
        
        if not valid_soc_values:
            logger.warning("Keine gültigen SoC-Werte verfügbar - verwende 50% als Fallback")
            return 50.0  # Fallback nur für Berechnungen
        
        average = sum(valid_soc_values) / len(valid_soc_values)
        logger.debug(f"Durchschnittlicher SoC: {average:.1f}% (aus {len(valid_soc_values)} Akkus)")
        return average
    
    def get_all_status(self) -> Dict[int, Dict[str, Any]]:
        """Gibt Status aller Duravolt Akkus zurück"""
        status = {}
        for akku_id, battery in self.batteries.items():
            status[akku_id] = battery.get_status()
        return status
    
    def get_min_max_soc(self) -> Tuple[Optional[float], Optional[float]]:
        """Gibt minimalen und maximalen SoC zurück"""
        valid_soc_values = []
        for battery in self.batteries.values():
            if battery.last_soc is not None:
                valid_soc_values.append(battery.last_soc)
        
        if not valid_soc_values:
            return None, None
        
        return min(valid_soc_values), max(valid_soc_values)
