#!/usr/bin/env python3
"""
Einfache Status-Website für Marstek PV-Akku Steuerung
Minimaler Flask-Server mit Live-Daten und Log-Anzeige
"""

import logging
import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from typing import Dict, Any
from templates import SETUP_HTML  # Import des Setup Templates
from web_config import CONFIG_HTML_TEMPLATE as CONFIG_HTML  # Import des Config Templates

logger = logging.getLogger(__name__)

class SimpleWebServer:
    """Einfacher Webserver für Status-Anzeige"""
    
    def __init__(self, shelly_client, battery_manager, controller, config):
        self.energy_meter = shelly_client  # Kann Shelly oder EcoTracker sein
        self.batteries = battery_manager
        self.controller = controller
        self.config = config
        
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.logger.setLevel(logging.WARNING)  # Flask-Logs reduzieren
        
        # Log-Puffer für Web-Anzeige
        self.log_buffer = []
        self.max_log_entries = 50
        
        self._setup_routes()
        logger.info("Web-Server initialisiert")
    
    def _setup_routes(self):
        """Erstellt Flask-Routen"""
        
        @self.app.route('/')
        def dashboard():
            """Haupt-Dashboard"""
            return render_template('dashboard.html')
        
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            """Statische Dateien servieren"""
            return send_from_directory('static', filename)
        
        @self.app.route('/api/status')
        def api_status():
            """API-Endpunkt für Live-Status"""
            try:
                # Energy Meter Status
                meter_status = self.energy_meter.get_status()
                current_power = self.energy_meter.get_power()
                
                # Battery-Status
                battery_status = self.batteries.get_all_status()
                total_battery_power = self.batteries.get_total_power()
                
                # Controller-Status
                controller_status = self.controller.get_status()
                controller_status['enabled'] = self.controller.enabled
                
                # Zusammenfassung
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'grid_power': current_power,
                    'battery_power': total_battery_power,
                    'resulting_power': (current_power or 0) - total_battery_power,
                    'energy_meter': meter_status,
                    'meter_type': self.config.get_energy_meter_type(),
                    'batteries': battery_status,
                    'controller': controller_status,
                    'system_status': self._get_system_status(meter_status, battery_status)
                }
                
                return jsonify(status)
                
            except Exception as e:
                logger.error(f"API-Status-Fehler: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        def api_logs():
            """API-Endpunkt für Log-Anzeige"""
            return jsonify({'logs': self.log_buffer})
        
        @self.app.route('/setup')
        def setup_page():
            """Setup-Seite für Modbus ID Konfiguration"""
            # Stoppe die Akku-Steuerung beim Betreten des Setup-Modus
            logger.warning("Setup-Modus aktiviert - Stoppe Akku-Steuerung")
            self.controller.enabled = False
            self.batteries.stop_all()
            self.add_log_entry('WARNING', 'Setup-Modus aktiviert - Akku-Steuerung gestoppt')
            return SETUP_HTML
        
        @self.app.route('/api/scan_modbus_ids', methods=['POST'])
        def scan_modbus_ids():
            """Scannt nach vorhandenen Modbus IDs"""
            try:
                data = request.get_json()
                battery_config = self.config.get_battery_config()
                ip = data.get('ip', battery_config.get('ip'))
                port = data.get('port', battery_config.get('port', 502))
                
                found_ids = []
                logger.info(f"Starte Modbus ID Scan auf {ip}:{port}")
                
                # Sicherstellen, dass die Steuerung gestoppt ist
                if self.controller.enabled:
                    self.controller.enabled = False
                    self.batteries.stop_all()
                    logger.warning("Akku-Steuerung für Scan gestoppt")
                
                from pymodbus.client import ModbusTcpClient
                
                # Scanne IDs 1-10
                for slave_id in range(1, 11):
                    try:
                        client = ModbusTcpClient(host=ip, port=port, timeout=1)
                        if client.connect():
                            # Versuche Register 41100 zu lesen
                            result = client.read_holding_registers(
                                address=41100,
                                count=1,
                                slave=slave_id
                            )
                            if not result.isError():
                                found_ids.append({
                                    'id': slave_id,
                                    'current_id': result.registers[0]
                                })
                                logger.info(f"Gefunden: Slave ID {slave_id}")
                            client.close()
                    except Exception as e:
                        pass
                
                logger.info(f"Scan abgeschlossen. Gefundene IDs: {[x['id'] for x in found_ids]}")
                return jsonify({
                    'success': True,
                    'found_ids': found_ids
                })
                
            except Exception as e:
                logger.error(f"Fehler beim ID-Scan: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/set_modbus_id', methods=['POST'])
        def set_modbus_id():
            """Setzt neue Modbus ID für Gerät mit ID 1"""
            try:
                data = request.get_json()
                new_id = data.get('new_id')
                battery_config = self.config.get_battery_config()
                ip = data.get('ip', battery_config.get('ip'))
                port = data.get('port', battery_config.get('port', 502))
                
                if not new_id or not (1 <= new_id <= 255):
                    return jsonify({'success': False, 'error': 'Ungültige ID (1-255)'}), 400
                
                logger.info(f"Setze Modbus ID 1 auf neue ID {new_id}")
                
                from pymodbus.client import ModbusTcpClient
                
                client = ModbusTcpClient(host=ip, port=port, timeout=3)
                if not client.connect():
                    return jsonify({'success': False, 'error': 'Verbindung fehlgeschlagen'}), 500
                
                try:
                    # Schreibe neue ID in Register 41100 für Slave ID 1
                    result = client.write_register(
                        address=41100,
                        value=new_id,
                        slave=1  # Immer an ID 1 senden
                    )
                    
                    if result.isError():
                        logger.error(f"Fehler beim Setzen der ID: {result}")
                        return jsonify({'success': False, 'error': f'Modbus-Fehler: {result}'}), 500
                    
                    logger.info(f"Modbus ID erfolgreich auf {new_id} gesetzt")
                    return jsonify({
                        'success': True,
                        'message': f'ID erfolgreich auf {new_id} gesetzt'
                    })
                    
                finally:
                    client.close()
                    
            except Exception as e:
                logger.error(f"Fehler beim Setzen der ID: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/resume_control', methods=['POST'])
        def resume_control():
            """Aktiviert die Akku-Steuerung wieder"""
            try:
                logger.info("Aktiviere Akku-Steuerung wieder")
                self.controller.enabled = True
                self.add_log_entry('INFO', 'Akku-Steuerung wieder aktiviert')
                return jsonify({'success': True, 'message': 'Steuerung aktiviert'})
            except Exception as e:
                logger.error(f"Fehler beim Aktivieren der Steuerung: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/config')
        def config_page():
            """Konfigurations-Seite"""
            logger.info("Config-Seite aufgerufen")
            return CONFIG_HTML
        
        @self.app.route('/api/get_battery_config')
        def get_battery_config():
            """Gibt die Akku-Konfiguration für das Setup zurück"""
            try:
                battery_config = self.config.get_battery_config()
                return jsonify({
                    'success': True,
                    'ip': battery_config.get('ip', ''),
                    'port': battery_config.get('port', 502)
                })
            except Exception as e:
                logger.error(f"Fehler beim Laden der Akku-Konfiguration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_config')
        def get_config():
            """Gibt aktuelle Konfiguration zurück"""
            try:
                import json
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return jsonify({'success': True, 'config': config_data})
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/save_config', methods=['POST'])
        def save_config():
            """Speichert neue Konfiguration"""
            try:
                import json
                new_config = request.get_json()
                
                # Backup der alten Konfiguration
                import shutil
                from datetime import datetime
                backup_name = f"config.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2('config.json', backup_name)
                logger.info(f"Backup erstellt: {backup_name}")
                
                # Neue Konfiguration speichern
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(new_config, f, indent=2, ensure_ascii=False)
                
                self.add_log_entry('INFO', 'Konfiguration gespeichert')
                return jsonify({'success': True, 'message': 'Konfiguration gespeichert'})
                
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/reload_config', methods=['POST'])
        def reload_config():
            """Lädt Konfiguration neu (teilweise)"""
            try:
                # Lade neue Konfiguration
                self.config.load()
                
                # Aktualisiere änderbare Parameter
                control_config = self.config.get_control_config()
                battery_config = self.config.get_battery_config()
                
                # Controller-Parameter aktualisieren
                self.controller.target_grid_power_charge = control_config.get('target_grid_power_charge', -20)
                self.controller.target_grid_power_discharge = control_config.get('target_grid_power_discharge', 20)
                self.controller.min_soc_discharge = battery_config['min_soc_for_discharge']
                self.controller.max_soc_charge = battery_config['max_soc_for_charge']
                
                # Hinweis: Einige Parameter (wie IP-Adressen, Akku-IDs) können nicht ohne Neustart geändert werden
                
                self.add_log_entry('INFO', 'Konfiguration teilweise neu geladen')
                return jsonify({
                    'success': True, 
                    'message': 'Einige Einstellungen wurden übernommen. Für vollständige Änderungen ist ein Neustart erforderlich.',
                    'reloadable': ['target_grid_power_charge', 'target_grid_power_discharge', 'min_soc_for_discharge', 'max_soc_for_charge']
                })
                
            except Exception as e:
                logger.error(f"Fehler beim Neuladen der Konfiguration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def _get_system_status(self, meter_status: Dict, battery_status: Dict) -> Dict[str, Any]:
        """Bestimmt Gesamt-Systemstatus"""
        meter_type = self.config.get_energy_meter_type()
        
        # Energy Meter Status prüfen
        if not meter_status.get('online', False):
            return {'status': 'error', 'message': f'{meter_type} offline'}
        
        if meter_status.get('failure_count', 0) > 0:
            return {'status': 'warning', 'message': f"{meter_type}-Fehler: {meter_status['failure_count']}"}
        
        # Battery-Status prüfen
        total_batteries = len(battery_status)
        error_batteries = sum(1 for b in battery_status.values() if b.get('error_count', 0) > 5)
        
        if error_batteries == total_batteries:
            return {'status': 'error', 'message': 'Alle Akkus fehlerhaft'}
        elif error_batteries > 0:
            return {'status': 'warning', 'message': f'{error_batteries}/{total_batteries} Akkus fehlerhaft'}
        
        return {'status': 'ok', 'message': 'System normal'}
    
    def add_log_entry(self, level: str, message: str):
        """Fügt Log-Eintrag zum Web-Puffer hinzu"""
        entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        }
        
        self.log_buffer.append(entry)
        
        # Puffer-Größe begrenzen
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer.pop(0)
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Startet den Webserver"""
        logger.info(f"Starte Web-Server auf {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)
