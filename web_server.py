#!/usr/bin/env python3
"""
Einfache Status-Website für Marstek PV-Akku Steuerung
Minimaler Flask-Server mit Live-Daten und Log-Anzeige
"""

import logging
import json
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SimpleWebServer:
    """Einfacher Webserver für Status-Anzeige"""
    
    def __init__(self, shelly_client, battery_manager, controller, config):
        self.energy_meter = shelly_client  # Kann Shelly oder EcoTracker sein
        self.batteries = battery_manager
        self.controller = controller
        self.config = config
        
        self.app = Flask(__name__)
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
            return render_template_string(DASHBOARD_HTML)
        
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
            return render_template_string(SETUP_HTML)
        
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
            return render_template_string(CONFIG_HTML)
        
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

# HTML-Template für Setup-Seite
SETUP_HTML = '''

# HTML-Template für Konfigurations-Seite
CONFIG_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marstek Configuration</title>
    <style>
        :root {
            --primary-color: #03a9f4;
            --accent-color: #ff9800;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --error-color: #f44336;
            --info-color: #2196f3;
            
            --bg-primary: #111111;
            --bg-secondary: #1c1c1c;
            --bg-card: #1c1c1c;
            --bg-card-hover: #242424;
            
            --text-primary: #e1e1e1;
            --text-secondary: #9e9e9e;
            --text-disabled: #6e6e6e;
            
            --border-color: #282828;
            --divider-color: #2c2c2c;
            
            --shadow-card: 0 2px 4px 0 rgba(0,0,0,0.5);
            --shadow-card-hover: 0 4px 8px 0 rgba(0,0,0,0.6);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }
        
        .config-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 400;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1rem;
        }
        
        .language-switcher {
            position: absolute;
            top: 0;
            right: 0;
            display: flex;
            gap: 0.5rem;
        }
        
        .language-button {
            padding: 0.375rem 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.75rem;
        }
        
        .language-button.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .nav-links {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            justify-content: center;
        }
        
        .nav-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }
        
        .nav-link:hover {
            background: var(--bg-card-hover);
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .config-section {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
        }
        
        .section-title {
            font-size: 1.25rem;
            font-weight: 500;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .form-group small {
            display: block;
            margin-top: 0.25rem;
            color: var(--text-disabled);
            font-size: 0.75rem;
        }
        
        .array-input {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            justify-content: center;
        }
        
        .button {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .button-primary {
            background: var(--primary-color);
            color: white;
        }
        
        .button-primary:hover {
            background: #0288d1;
        }
        
        .button-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .button-secondary:hover {
            background: var(--bg-card-hover);
        }
        
        .button-success {
            background: var(--success-color);
            color: white;
        }
        
        .button-success:hover {
            background: #388e3c;
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .status-message {
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            text-align: center;
            display: none;
        }
        
        .status-success {
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid var(--success-color);
            color: var(--success-color);
        }
        
        .status-error {
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid var(--error-color);
            color: var(--error-color);
        }
        
        .status-warning {
            background: rgba(255, 152, 0, 0.1);
            border: 1px solid var(--warning-color);
            color: var(--warning-color);
        }
        
        .info-box {
            background: rgba(33, 150, 243, 0.1);
            border: 1px solid var(--info-color);
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .info-box h3 {
            color: var(--info-color);
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .info-box ul {
            margin-left: 1.5rem;
            color: var(--text-secondary);
        }
        
        .json-editor {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
            line-height: 1.5;
            tab-size: 2;
        }
        
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s linear infinite;
            margin-left: 0.5rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="config-container">
        <div class="header">
            <div class="language-switcher">
                <button class="language-button active" onclick="setLanguage('de')" data-lang="de">DE</button>
                <button class="language-button" onclick="setLanguage('en')" data-lang="en">EN</button>
            </div>
            <h1>⚙️ <span data-i18n="title">Konfiguration</span></h1>
            <p data-i18n="subtitle">Marstek PV-Akku Steuerung Einstellungen</p>
        </div>
        
        <div class="nav-links">
            <a href="/" class="nav-link">
                ← <span data-i18n="backToDashboard">Zurück zum Dashboard</span>
            </a>
            <a href="/setup" class="nav-link">
                🆔 <span data-i18n="toSetup">Zum Setup</span>
            </a>
            <a href="/config" class="nav-link">
                ⚙️ <span data-i18n="toConfig">Zur Konfiguration</span>
            </a>
        </div>
        
        <div class="status-message" id="statusMessage"></div>
        
        <div class="info-box">
            <h3>ℹ️ <span data-i18n="infoTitle">Wichtige Informationen</span></h3>
            <ul>
                <li data-i18n="info1">Einige Einstellungen erfordern einen Neustart der Anwendung</li>
                <li data-i18n="info2">Die alte Konfiguration wird automatisch gesichert</li>
                <li data-i18n="info3">Grün markierte Felder können ohne Neustart übernommen werden</li>
            </ul>
        </div>
        
        <!-- Energy Meter Section -->
        <div class="config-section">
            <h2 class="section-title">📊 <span data-i18n="energyMeterSection">Energiemessgerät</span></h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="meterType" data-i18n="meterTypeLabel">Typ</label>
                    <select id="meterType" onchange="toggleMeterConfig()">
                        <option value="shelly">Shelly 3EM Pro</option>
                        <option value="ecotracker">EcoTracker</option>
                    </select>
                </div>
            </div>
            
            <!-- Shelly Config -->
            <div id="shellyConfig">
                <h3>Shelly 3EM Pro</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="shellyIp">IP-Adresse</label>
                        <input type="text" id="shellyIp" placeholder="192.168.1.100">
                    </div>
                    <div class="form-group">
                        <label for="shellyTimeout">Timeout (s)</label>
                        <input type="number" id="shellyTimeout" min="1" max="30" value="5">
                    </div>
                    <div class="form-group">
                        <label for="shellyMaxFailures" data-i18n="maxFailuresLabel">Max. Fehler vor Stopp</label>
                        <input type="number" id="shellyMaxFailures" min="1" max="10" value="2">
                    </div>
                </div>
            </div>
            
            <!-- EcoTracker Config -->
            <div id="ecotrackerConfig" style="display: none;">
                <h3>EcoTracker</h3>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="ecoIp">IP-Adresse</label>
                        <input type="text" id="ecoIp" placeholder="192.168.1.101">
                    </div>
                    <div class="form-group">
                        <label for="ecoTimeout">Timeout (s)</label>
                        <input type="number" id="ecoTimeout" min="1" max="30" value="5">
                    </div>
                    <div class="form-group">
                        <label for="ecoMaxFailures" data-i18n="maxFailuresLabel">Max. Fehler vor Stopp</label>
                        <input type="number" id="ecoMaxFailures" min="1" max="10" value="2">
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Battery Section -->
        <div class="config-section">
            <h2 class="section-title">🔋 <span data-i18n="batterySection">Batteriespeicher</span></h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="batteryIp">Modbus TCP IP</label>
                    <input type="text" id="batteryIp" placeholder="192.168.1.200">
                </div>
                <div class="form-group">
                    <label for="batteryPort">Modbus TCP Port</label>
                    <input type="number" id="batteryPort" min="1" max="65535" value="502">
                </div>
                <div class="form-group">
                    <label for="akkuIds" data-i18n="akkuIdsLabel">Akku IDs (kommagetrennt)</label>
                    <input type="text" id="akkuIds" placeholder="1,2,3">
                    <small data-i18n="akkuIdsHelp">Beispiel: 1 oder 1,2,3</small>
                </div>
                <div class="form-group">
                    <label for="maxPowerPerBattery" data-i18n="maxPowerLabel">Max. Leistung pro Akku (W)</label>
                    <input type="number" id="maxPowerPerBattery" min="100" max="5000" value="2500">
                </div>
                <div class="form-group">
                    <label for="minPowerPerBattery" data-i18n="minPowerLabel">Min. Leistung pro Akku (W)</label>
                    <input type="number" id="minPowerPerBattery" min="10" max="500" value="50">
                </div>
                <div class="form-group" style="background: rgba(76, 175, 80, 0.1); padding: 0.5rem; border-radius: 6px;">
                    <label for="minSocDischarge" data-i18n="minSocLabel">Min. SoC für Entladung (%)</label>
                    <input type="number" id="minSocDischarge" min="0" max="50" value="11">
                    <small data-i18n="reloadable">✓ Ohne Neustart änderbar</small>
                </div>
                <div class="form-group" style="background: rgba(76, 175, 80, 0.1); padding: 0.5rem; border-radius: 6px;">
                    <label for="maxSocCharge" data-i18n="maxSocLabel">Max. SoC für Ladung (%)</label>
                    <input type="number" id="maxSocCharge" min="50" max="100" value="98">
                    <small data-i18n="reloadable">✓ Ohne Neustart änderbar</small>
                </div>
            </div>
        </div>
        
        <!-- Control Section -->
        <div class="config-section">
            <h2 class="section-title">🎯 <span data-i18n="controlSection">Regelungsparameter</span></h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="pollInterval" data-i18n="pollIntervalLabel">Regelungsintervall (s)</label>
                    <input type="number" id="pollInterval" min="1" max="10" value="2" step="0.5">
                </div>
                <div class="form-group">
                    <label for="socUpdateInterval" data-i18n="socUpdateLabel">SoC-Update Intervall (s)</label>
                    <input type="number" id="socUpdateInterval" min="10" max="300" value="30">
                </div>
                <div class="form-group" style="background: rgba(76, 175, 80, 0.1); padding: 0.5rem; border-radius: 6px;">
                    <label for="targetGridCharge" data-i18n="targetChargeLabel">Ziel-Netzleistung Laden (W)</label>
                    <input type="number" id="targetGridCharge" min="-500" max="0" value="-20">
                    <small data-i18n="reloadable">✓ Ohne Neustart änderbar</small>
                </div>
                <div class="form-group" style="background: rgba(76, 175, 80, 0.1); padding: 0.5rem; border-radius: 6px;">
                    <label for="targetGridDischarge" data-i18n="targetDischargeLabel">Ziel-Netzleistung Entladen (W)</label>
                    <input type="number" id="targetGridDischarge" min="0" max="500" value="20">
                    <small data-i18n="reloadable">✓ Ohne Neustart änderbar</small>
                </div>
            </div>
        </div>
        
        <!-- Web Server Section -->
        <div class="config-section">
            <h2 class="section-title">🌐 <span data-i18n="webSection">Web-Server</span></h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="webHost">Host</label>
                    <input type="text" id="webHost" value="0.0.0.0">
                    <small data-i18n="webHostHelp">0.0.0.0 = alle Netzwerkschnittstellen</small>
                </div>
                <div class="form-group">
                    <label for="webPort">Port</label>
                    <input type="number" id="webPort" min="1" max="65535" value="8080">
                </div>
            </div>
        </div>
        
        <!-- Logging Section -->
        <div class="config-section">
            <h2 class="section-title">📋 <span data-i18n="loggingSection">Logging</span></h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="logLevel">Log-Level</label>
                    <select id="logLevel">
                        <option value="DEBUG">DEBUG</option>
                        <option value="INFO" selected>INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="logFile" data-i18n="logFileLabel">Log-Datei</label>
                    <input type="text" id="logFile" value="logs/marstek.log">
                </div>
                <div class="form-group">
                    <label for="logMaxSize" data-i18n="logMaxSizeLabel">Max. Dateigröße (MB)</label>
                    <input type="number" id="logMaxSize" min="1" max="100" value="10">
                </div>
            </div>
        </div>
        
        <div class="button-group">
            <button class="button button-secondary" onclick="loadConfig()">
                <span data-i18n="reloadButton">Konfiguration neu laden</span>
            </button>
            <button class="button button-primary" onclick="saveConfig()">
                <span data-i18n="saveButton">Speichern</span>
            </button>
            <button class="button button-success" onclick="reloadConfig()">
                <span data-i18n="applyButton">Einige Einstellungen übernehmen</span>
            </button>
        </div>
    </div>
    
    <script>
        let currentLanguage = 'de';
        let originalConfig = {};
        
        // Übersetzungen
        const translations = {
            de: {
                title: 'Konfiguration',
                subtitle: 'Marstek PV-Akku Steuerung Einstellungen',
                backToDashboard: 'Zurück zum Dashboard',
                toSetup: 'Zum Setup',
                infoTitle: 'Wichtige Informationen',
                info1: 'Einige Einstellungen erfordern einen Neustart der Anwendung',
                info2: 'Die alte Konfiguration wird automatisch gesichert',
                info3: 'Grün markierte Felder können ohne Neustart übernommen werden',
                energyMeterSection: 'Energiemessgerät',
                meterTypeLabel: 'Typ',
                maxFailuresLabel: 'Max. Fehler vor Stopp',
                batterySection: 'Batteriespeicher',
                akkuIdsLabel: 'Akku IDs (kommagetrennt)',
                akkuIdsHelp: 'Beispiel: 1 oder 1,2,3',
                maxPowerLabel: 'Max. Leistung pro Akku (W)',
                minPowerLabel: 'Min. Leistung pro Akku (W)',
                minSocLabel: 'Min. SoC für Entladung (%)',
                maxSocLabel: 'Max. SoC für Ladung (%)',
                reloadable: '✓ Ohne Neustart änderbar',
                controlSection: 'Regelungsparameter',
                pollIntervalLabel: 'Regelungsintervall (s)',
                socUpdateLabel: 'SoC-Update Intervall (s)',
                targetChargeLabel: 'Ziel-Netzleistung Laden (W)',
                targetDischargeLabel: 'Ziel-Netzleistung Entladen (W)',
                webSection: 'Web-Server',
                webHostHelp: '0.0.0.0 = alle Netzwerkschnittstellen',
                loggingSection: 'Logging',
                logFileLabel: 'Log-Datei',
                logMaxSizeLabel: 'Max. Dateigröße (MB)',
                reloadButton: 'Konfiguration neu laden',
                saveButton: 'Speichern',
                applyButton: 'Einige Einstellungen übernehmen',
                loadingConfig: 'Lade Konfiguration...',
                savingConfig: 'Speichere Konfiguration...',
                applyingConfig: 'Übernehme Einstellungen...',
                successLoaded: 'Konfiguration geladen',
                successSaved: 'Konfiguration gespeichert. Neustart erforderlich für vollständige Übernahme.',
                successApplied: 'Einige Einstellungen wurden übernommen.',
                errorLoading: 'Fehler beim Laden:',
                errorSaving: 'Fehler beim Speichern:',
                errorApplying: 'Fehler beim Übernehmen:',
                restartInfo: 'Die folgenden Einstellungen wurden geändert und erfordern einen Neustart:',
                confirmRestart: 'Möchten Sie die Anwendung jetzt neu starten?'
            },
            en: {
                title: 'Configuration',
                subtitle: 'Marstek PV Battery Control Settings',
                backToDashboard: 'Back to Dashboard',
                toSetup: 'To Setup',
                infoTitle: 'Important Information',
                info1: 'Some settings require an application restart',
                info2: 'The old configuration will be backed up automatically',
                info3: 'Green marked fields can be applied without restart',
                energyMeterSection: 'Energy Meter',
                meterTypeLabel: 'Type',
                maxFailuresLabel: 'Max. failures before stop',
                batterySection: 'Battery Storage',
                akkuIdsLabel: 'Battery IDs (comma separated)',
                akkuIdsHelp: 'Example: 1 or 1,2,3',
                maxPowerLabel: 'Max. power per battery (W)',
                minPowerLabel: 'Min. power per battery (W)',
                minSocLabel: 'Min. SoC for discharge (%)',
                maxSocLabel: 'Max. SoC for charge (%)',
                reloadable: '✓ Changeable without restart',
                controlSection: 'Control Parameters',
                pollIntervalLabel: 'Control interval (s)',
                socUpdateLabel: 'SoC update interval (s)',
                targetChargeLabel: 'Target grid power charging (W)',
                targetDischargeLabel: 'Target grid power discharging (W)',
                webSection: 'Web Server',
                webHostHelp: '0.0.0.0 = all network interfaces',
                loggingSection: 'Logging',
                logFileLabel: 'Log file',
                logMaxSizeLabel: 'Max. file size (MB)',
                reloadButton: 'Reload configuration',
                saveButton: 'Save',
                applyButton: 'Apply some settings',
                loadingConfig: 'Loading configuration...',
                savingConfig: 'Saving configuration...',
                applyingConfig: 'Applying settings...',
                successLoaded: 'Configuration loaded',
                successSaved: 'Configuration saved. Restart required for full application.',
                successApplied: 'Some settings have been applied.',
                errorLoading: 'Error loading:',
                errorSaving: 'Error saving:',
                errorApplying: 'Error applying:',
                restartInfo: 'The following settings have been changed and require a restart:',
                confirmRestart: 'Do you want to restart the application now?'
            }
        };
        
        // Sprache setzen
        function setLanguage(lang) {
            currentLanguage = lang;
            
            // Buttons aktualisieren
            document.querySelectorAll('.language-button').forEach(btn => {
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Übersetzungen anwenden
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                if (translations[lang][key]) {
                    element.textContent = translations[lang][key];
                }
            });
            
            // localStorage speichern
            localStorage.setItem('language', lang);
        }
        
        // Hilfsfunktion für Übersetzungen
        function t(key) {
            return translations[currentLanguage][key] || key;
        }
        
        function toggleMeterConfig() {
            const meterType = document.getElementById('meterType').value;
            document.getElementById('shellyConfig').style.display = meterType === 'shelly' ? 'block' : 'none';
            document.getElementById('ecotrackerConfig').style.display = meterType === 'ecotracker' ? 'block' : 'none';
        }
        
        function showStatus(type, message) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.style.display = 'block';
            
            if (type === 'success') {
                setTimeout(() => {
                    statusEl.style.display = 'none';
                }, 5000);
            }
        }
        
        function loadConfig() {
            showStatus('info', t('loadingConfig'));
            
            fetch('/api/get_config')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        originalConfig = data.config;
                        populateForm(data.config);
                        showStatus('success', t('successLoaded'));
                    } else {
                        showStatus('error', t('errorLoading') + ' ' + data.error);
                    }
                })
                .catch(error => {
                    showStatus('error', t('errorLoading') + ' ' + error);
                });
        }
        
        function populateForm(config) {
            // Energy Meter
            document.getElementById('meterType').value = config.energy_meter?.type || 'shelly';
            toggleMeterConfig();
            
            // Shelly
            document.getElementById('shellyIp').value = config.shelly?.ip || '';
            document.getElementById('shellyTimeout').value = config.shelly?.timeout_seconds || 5;
            document.getElementById('shellyMaxFailures').value = config.shelly?.max_failures_before_stop || 2;
            
            // EcoTracker
            document.getElementById('ecoIp').value = config.ecotracker?.ip || '';
            document.getElementById('ecoTimeout').value = config.ecotracker?.timeout_seconds || 5;
            document.getElementById('ecoMaxFailures').value = config.ecotracker?.max_failures_before_stop || 2;
            
            // Battery
            document.getElementById('batteryIp').value = config.battery?.ip || '';
            document.getElementById('batteryPort').value = config.battery?.port || 502;
            document.getElementById('akkuIds').value = config.battery?.akku_ids?.join(',') || '';
            document.getElementById('maxPowerPerBattery').value = config.battery?.max_power_per_battery || 2500;
            document.getElementById('minPowerPerBattery').value = config.battery?.min_power_per_battery || 50;
            document.getElementById('minSocDischarge').value = config.battery?.min_soc_for_discharge || 11;
            document.getElementById('maxSocCharge').value = config.battery?.max_soc_for_charge || 98;
            
            // Control
            document.getElementById('pollInterval').value = config.control?.poll_interval_seconds || 2;
            document.getElementById('socUpdateInterval').value = config.control?.soc_update_interval_seconds || 30;
            document.getElementById('targetGridCharge').value = config.control?.target_grid_power_charge || -20;
            document.getElementById('targetGridDischarge').value = config.control?.target_grid_power_discharge || 20;
            
            // Web
            document.getElementById('webHost').value = config.web?.host || '0.0.0.0';
            document.getElementById('webPort').value = config.web?.port || 8080;
            
            // Logging
            document.getElementById('logLevel').value = config.logging?.level || 'INFO';
            document.getElementById('logFile').value = config.logging?.file || 'logs/marstek.log';
            document.getElementById('logMaxSize').value = config.logging?.max_size_mb || 10;
        }
        
        function buildConfig() {
            const akkuIdsText = document.getElementById('akkuIds').value;
            const akkuIds = akkuIdsText.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
            
            return {
                energy_meter: {
                    type: document.getElementById('meterType').value,
                    comment: "Verfügbare Typen: 'shelly' oder 'ecotracker'"
                },
                shelly: {
                    ip: document.getElementById('shellyIp').value,
                    timeout_seconds: parseInt(document.getElementById('shellyTimeout').value),
                    max_failures_before_stop: parseInt(document.getElementById('shellyMaxFailures').value)
                },
                ecotracker: {
                    ip: document.getElementById('ecoIp').value,
                    timeout_seconds: parseInt(document.getElementById('ecoTimeout').value),
                    max_failures_before_stop: parseInt(document.getElementById('ecoMaxFailures').value)
                },
                battery: {
                    ip: document.getElementById('batteryIp').value,
                    port: parseInt(document.getElementById('batteryPort').value),
                    akku_ids: akkuIds,
                    max_power_per_battery: parseInt(document.getElementById('maxPowerPerBattery').value),
                    min_power_per_battery: parseInt(document.getElementById('minPowerPerBattery').value),
                    min_soc_for_discharge: parseInt(document.getElementById('minSocDischarge').value),
                    max_soc_for_charge: parseInt(document.getElementById('maxSocCharge').value)
                },
                control: {
                    poll_interval_seconds: parseFloat(document.getElementById('pollInterval').value),
                    soc_update_interval_seconds: parseInt(document.getElementById('socUpdateInterval').value),
                    target_grid_power_charge: parseInt(document.getElementById('targetGridCharge').value),
                    target_grid_power_discharge: parseInt(document.getElementById('targetGridDischarge').value)
                },
                web: {
                    host: document.getElementById('webHost').value,
                    port: parseInt(document.getElementById('webPort').value)
                },
                logging: {
                    level: document.getElementById('logLevel').value,
                    file: document.getElementById('logFile').value,
                    max_size_mb: parseInt(document.getElementById('logMaxSize').value),
                    backup_count: 3
                }
            };
        }
        
        function saveConfig() {
            showStatus('info', t('savingConfig'));
            
            const config = buildConfig();
            
            fetch('/api/save_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', t('successSaved'));
                    originalConfig = config;
                } else {
                    showStatus('error', t('errorSaving') + ' ' + data.error);
                }
            })
            .catch(error => {
                showStatus('error', t('errorSaving') + ' ' + error);
            });
        }
        
        function reloadConfig() {
            showStatus('info', t('applyingConfig'));
            
            fetch('/api/reload_config', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('warning', data.message);
                } else {
                    showStatus('error', t('errorApplying') + ' ' + data.error);
                }
            })
            .catch(error => {
                showStatus('error', t('errorApplying') + ' ' + error);
            });
        }
        
        // Initialisierung
        window.addEventListener('load', () => {
            // Gespeicherte Sprache laden
            const savedLang = localStorage.getItem('language') || 'de';
            setLanguage(savedLang);
            
            // Konfiguration laden
            loadConfig();
        });
    </script>
</body>
</html>
'''

# HTML-Template für Konfigurations-Seite
CONFIG_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marstek Configuration</title>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marstek Modbus ID Setup</title>
    <style>
        :root {
            --primary-color: #03a9f4;
            --accent-color: #ff9800;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --error-color: #f44336;
            --info-color: #2196f3;
            
            --bg-primary: #111111;
            --bg-secondary: #1c1c1c;
            --bg-card: #1c1c1c;
            --bg-card-hover: #242424;
            
            --text-primary: #e1e1e1;
            --text-secondary: #9e9e9e;
            --text-disabled: #6e6e6e;
            
            --border-color: #282828;
            --divider-color: #2c2c2c;
            
            --shadow-card: 0 2px 4px 0 rgba(0,0,0,0.5);
            --shadow-card-hover: 0 4px 8px 0 rgba(0,0,0,0.6);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        
        .setup-container {
            max-width: 800px;
            width: 100%;
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2.5rem;
            box-shadow: var(--shadow-card);
            border: 1px solid var(--border-color);
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 400;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1rem;
        }
        
        .back-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--primary-color);
            text-decoration: none;
            margin-bottom: 2rem;
            font-size: 0.875rem;
        }
        
        .back-link:hover {
            text-decoration: underline;
        }
        
        .section {
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .section-title {
            font-size: 1.25rem;
            font-weight: 500;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .warning-box {
            background: rgba(255, 152, 0, 0.1);
            border: 1px solid var(--warning-color);
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .warning-box h3 {
            color: var(--warning-color);
            font-size: 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .warning-box ul {
            margin-left: 1.5rem;
            color: var(--text-secondary);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .button {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .button-primary {
            background: var(--primary-color);
            color: white;
        }
        
        .button-primary:hover {
            background: #0288d1;
        }
        
        .button-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .button-secondary:hover {
            background: var(--bg-card-hover);
        }
        
        .button-danger {
            background: var(--error-color);
            color: white;
        }
        
        .button-danger:hover {
            background: #d32f2f;
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .scan-results {
            margin-top: 1rem;
        }
        
        .device-list {
            display: grid;
            gap: 0.5rem;
        }
        
        .device-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }
        
        .device-item.highlight {
            border-color: var(--primary-color);
            background: rgba(3, 169, 244, 0.1);
        }
        
        .status-message {
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
            display: none;
        }
        
        .status-success {
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid var(--success-color);
            color: var(--success-color);
        }
        
        .status-error {
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid var(--error-color);
            color: var(--error-color);
        }
        
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s linear infinite;
            margin-left: 0.5rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: var(--bg-card);
            padding: 2rem;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            border: 1px solid var(--border-color);
        }
        
        .modal-header {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--warning-color);
        }
        
        .modal-body {
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }
        
        .language-switcher {
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .language-button {
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.875rem;
        }
        
        .language-button.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .language-button:hover:not(.active) {
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }
    </style>
</head>
<body>
    <div class="setup-container">
        <div class="language-switcher">
            <button class="language-button active" onclick="setLanguage('de')" data-lang="de">DE</button>
            <button class="language-button" onclick="setLanguage('en')" data-lang="en">EN</button>
        </div>
        
        <a href="/" class="back-link" onclick="confirmExit(event)">
            <span data-i18n="backToDashboard">← Zurück zum Dashboard</span>
        </a>
        
        <div class="header">
            <h1>⚙️ <span data-i18n="title">Modbus ID Setup</span></h1>
            <p data-i18n="subtitle">Konfiguration der Modbus Slave IDs für neue Geräte</p>
        </div>
        
        <div class="warning-box" style="margin-bottom: 2rem; background: rgba(244, 67, 54, 0.1); border-color: var(--error-color);">
            <h3 style="color: var(--error-color);">⚠️ <span data-i18n="warningTitle">Achtung: Akku-Steuerung gestoppt!</span></h3>
            <p data-i18n="warningText1">Die automatische Akku-Steuerung wurde für den Setup-Modus deaktiviert.</p>
            <p data-i18n="warningText2">Die Akkus werden erst wieder gesteuert, wenn Sie den Setup-Modus verlassen.</p>
            <button class="button button-primary" onclick="exitSetupMode()" style="margin-top: 1rem;">
                🏁 <span data-i18n="exitSetupMode">Setup-Modus beenden und Steuerung fortsetzen</span>
            </button>
        </div>
        
        <div class="section">
            <h2 class="section-title">🔍 <span data-i18n="step1Title">Schritt 1: Vorhandene Geräte scannen</span></h2>
            
            <p style="color: var(--text-secondary); margin-bottom: 1rem;" data-i18n="step1Description">
                Prüft welche Modbus IDs bereits vergeben sind (scannt IDs 1-10).
            </p>
            
            <button class="button button-primary" onclick="scanDevices()" id="scanButton">
                <span data-i18n="scanButton">Geräte scannen</span>
            </button>
            
            <div class="scan-results" id="scanResults" style="display: none;">
                <h3 style="margin-bottom: 0.5rem;" data-i18n="foundDevices">Gefundene Geräte:</h3>
                <div class="device-list" id="deviceList"></div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🆔 <span data-i18n="step2Title">Schritt 2: Neue ID vergeben</span></h2>
            
            <div class="warning-box">
                <h3>⚠️ <span data-i18n="importantNotes">Wichtige Hinweise:</span></h3>
                <ul>
                    <li data-i18n="note1">Alle neuen Akkus werden mit Slave ID 1 ausgeliefert</li>
                    <li data-i18n="note2">Es darf nur <strong>EIN</strong> neuer Akku mit ID 1 angeschlossen sein</li>
                    <li data-i18n="note3">Trennen Sie alle anderen neuen Akkus vor dem Setzen der ID</li>
                    <li data-i18n="note4">Nach dem Setzen muss die neue ID in der config.json eingetragen werden</li>
                </ul>
            </div>
            
            <div class="form-group">
                <label for="newId" data-i18n="newIdLabel">Neue Modbus ID (1-255):</label>
                <input type="number" id="newId" min="1" max="255" value="2" />
            </div>
            
            <button class="button button-danger" onclick="showConfirmModal()" id="setButton">
                <span data-i18n="setIdButton">ID 1 → neue ID setzen</span>
            </button>
            
            <div class="status-message" id="statusMessage"></div>
        </div>
    </div>
    
    <!-- Confirmation Modal -->
    <div class="modal" id="confirmModal">
        <div class="modal-content">
            <h3 class="modal-header">⚠️ <span data-i18n="confirmTitle">Sicherheitsabfrage</span></h3>
            <div class="modal-body">
                <p><strong data-i18n="confirmPrompt">Bitte bestätigen Sie:</strong></p>
                <ul>
                    <li data-i18n="confirm1">Es ist nur EIN neuer Akku mit ID 1 angeschlossen</li>
                    <li data-i18n="confirm2">Alle anderen neuen Akkus sind getrennt</li>
                    <li data-i18n="confirm3">Die neue ID ist noch nicht vergeben</li>
                </ul>
                <p style="margin-top: 1rem;" data-i18n="cannotUndo">Die Aktion kann nicht rückgängig gemacht werden!</p>
            </div>
            <div class="button-group">
                <button class="button button-secondary" onclick="hideConfirmModal()">
                    <span data-i18n="cancelButton">Abbrechen</span>
                </button>
                <button class="button button-danger" onclick="setModbusId()">
                    <span data-i18n="confirmButton">Bestätigen und ID setzen</span>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        let foundDevices = [];
        let currentLanguage = 'de';
        
        // Übersetzungen
        const translations = {
            de: {
                backToDashboard: '← Zurück zum Dashboard',
                title: 'Modbus ID Setup',
                subtitle: 'Konfiguration der Modbus Slave IDs für neue Geräte',
                warningTitle: 'Achtung: Akku-Steuerung gestoppt!',
                warningText1: 'Die automatische Akku-Steuerung wurde für den Setup-Modus deaktiviert.',
                warningText2: 'Die Akkus werden erst wieder gesteuert, wenn Sie den Setup-Modus verlassen.',
                exitSetupMode: 'Setup-Modus beenden und Steuerung fortsetzen',
                step1Title: 'Schritt 1: Vorhandene Geräte scannen',
                step1Description: 'Prüft welche Modbus IDs bereits vergeben sind (scannt IDs 1-10).',
                scanButton: 'Geräte scannen',
                scanning: 'Scanne...',
                foundDevices: 'Gefundene Geräte:',
                noDevicesFound: 'Keine Geräte gefunden',
                slaveId: 'Slave ID',
                register: 'Register',
                step2Title: 'Schritt 2: Neue ID vergeben',
                importantNotes: 'Wichtige Hinweise:',
                note1: 'Alle neuen Akkus werden mit Slave ID 1 ausgeliefert',
                note2: 'Es darf nur <strong>EIN</strong> neuer Akku mit ID 1 angeschlossen sein',
                note3: 'Trennen Sie alle anderen neuen Akkus vor dem Setzen der ID',
                note4: 'Nach dem Setzen muss die neue ID in der config.json eingetragen werden',
                newIdLabel: 'Neue Modbus ID (1-255):',
                setIdButton: 'ID 1 → neue ID setzen',
                settingId: 'Setze ID...',
                confirmTitle: 'Sicherheitsabfrage',
                confirmPrompt: 'Bitte bestätigen Sie:',
                confirm1: 'Es ist nur EIN neuer Akku mit ID 1 angeschlossen',
                confirm2: 'Alle anderen neuen Akkus sind getrennt',
                confirm3: 'Die neue ID ist noch nicht vergeben',
                cannotUndo: 'Die Aktion kann nicht rückgängig gemacht werden!',
                cancelButton: 'Abbrechen',
                confirmButton: 'Bestätigen und ID setzen',
                errorScanning: 'Fehler beim Scannen:',
                errorConnection: 'Verbindungsfehler:',
                errorInvalidId: 'Bitte gültige ID zwischen 1 und 255 eingeben',
                errorIdExists: 'ID {id} ist bereits vergeben!',
                successMessage: 'Erfolgreich! Gerät hat jetzt ID {id}. Bitte tragen Sie die ID in die config.json ein und starten Sie das System neu.',
                errorSettingId: 'Fehler:',
                confirmExit: 'Möchten Sie den Setup-Modus verlassen und die Akku-Steuerung wieder aktivieren?',
                controlResuming: 'Akku-Steuerung wird wieder aktiviert...',
                exitWarning: 'Die Akku-Steuerung ist noch deaktiviert. Möchten Sie wirklich die Seite verlassen?'
            },
            en: {
                backToDashboard: '← Back to Dashboard',
                title: 'Modbus ID Setup',
                subtitle: 'Configuration of Modbus Slave IDs for new devices',
                warningTitle: 'Warning: Battery control stopped!',
                warningText1: 'The automatic battery control has been disabled for setup mode.',
                warningText2: 'The batteries will only be controlled again when you exit setup mode.',
                exitSetupMode: 'Exit setup mode and resume control',
                step1Title: 'Step 1: Scan existing devices',
                step1Description: 'Checks which Modbus IDs are already assigned (scans IDs 1-10).',
                scanButton: 'Scan devices',
                scanning: 'Scanning...',
                foundDevices: 'Found devices:',
                noDevicesFound: 'No devices found',
                slaveId: 'Slave ID',
                register: 'Register',
                step2Title: 'Step 2: Assign new ID',
                importantNotes: 'Important notes:',
                note1: 'All new batteries are delivered with Slave ID 1',
                note2: 'Only <strong>ONE</strong> new battery with ID 1 must be connected',
                note3: 'Disconnect all other new batteries before setting the ID',
                note4: 'After setting, the new ID must be entered in config.json',
                newIdLabel: 'New Modbus ID (1-255):',
                setIdButton: 'ID 1 → set new ID',
                settingId: 'Setting ID...',
                confirmTitle: 'Security confirmation',
                confirmPrompt: 'Please confirm:',
                confirm1: 'Only ONE new battery with ID 1 is connected',
                confirm2: 'All other new batteries are disconnected',
                confirm3: 'The new ID is not yet assigned',
                cannotUndo: 'This action cannot be undone!',
                cancelButton: 'Cancel',
                confirmButton: 'Confirm and set ID',
                errorScanning: 'Error scanning:',
                errorConnection: 'Connection error:',
                errorInvalidId: 'Please enter a valid ID between 1 and 255',
                errorIdExists: 'ID {id} is already assigned!',
                successMessage: 'Success! Device now has ID {id}. Please enter the ID in config.json and restart the system.',
                errorSettingId: 'Error:',
                confirmExit: 'Do you want to exit setup mode and reactivate battery control?',
                controlResuming: 'Battery control is being reactivated...',
                exitWarning: 'Battery control is still disabled. Do you really want to leave the page?'
            }
        };
        
        // Sprache setzen
        function setLanguage(lang) {
            currentLanguage = lang;
            
            // Buttons aktualisieren
            document.querySelectorAll('.language-button').forEach(btn => {
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Übersetzungen anwenden
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                if (translations[lang][key]) {
                    element.innerHTML = translations[lang][key];
                }
            });
            
            // localStorage speichern (beide Keys für Kompatibilität)
            localStorage.setItem('language', lang);
            localStorage.setItem('setupLanguage', lang);
        }
        
        // Hilfsfunktion für Übersetzungen mit Variablen
        function t(key, vars = {}) {
            let text = translations[currentLanguage][key] || key;
            Object.keys(vars).forEach(varKey => {
                text = text.replace(`{${varKey}}`, vars[varKey]);
            });
            return text;
        }
        
        function scanDevices() {
            const button = document.getElementById('scanButton');
            const results = document.getElementById('scanResults');
            const deviceList = document.getElementById('deviceList');
            
            button.disabled = true;
            button.innerHTML = `<span data-i18n="scanning">${t('scanning')}</span> <span class="loader"></span>`;
            
            fetch('/api/scan_modbus_ids', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                button.disabled = false;
                button.innerHTML = `<span data-i18n="scanButton">${t('scanButton')}</span>`;
                
                if (data.success) {
                    foundDevices = data.found_ids;
                    results.style.display = 'block';
                    
                    if (foundDevices.length === 0) {
                        deviceList.innerHTML = `<p style="color: var(--text-secondary);">${t('noDevicesFound')}</p>`;
                    } else {
                        deviceList.innerHTML = foundDevices.map(device => `
                            <div class="device-item ${device.id === 1 ? 'highlight' : ''}">
                                <span>${t('slaveId')}: ${device.id}</span>
                                <span style="color: var(--text-secondary);">${t('register')} 41100: ${device.current_id}</span>
                            </div>
                        `).join('');
                        
                        // Automatisch nächste freie ID vorschlagen
                        const usedIds = foundDevices.map(d => d.id);
                        let nextFreeId = 2;
                        while (usedIds.includes(nextFreeId) && nextFreeId <= 10) {
                            nextFreeId++;
                        }
                        document.getElementById('newId').value = nextFreeId;
                    }
                } else {
                    showStatus('error', t('errorScanning') + ' ' + data.error);
                }
            })
            .catch(error => {
                button.disabled = false;
                button.innerHTML = `<span data-i18n="scanButton">${t('scanButton')}</span>`;
                showStatus('error', t('errorConnection') + ' ' + error);
            });
        }
        
        function showConfirmModal() {
            const newId = parseInt(document.getElementById('newId').value);
            
            if (!newId || newId < 1 || newId > 255) {
                showStatus('error', t('errorInvalidId'));
                return;
            }
            
            // Prüfe ob ID bereits vergeben
            const idExists = foundDevices.some(d => d.id === newId);
            if (idExists) {
                showStatus('error', t('errorIdExists', {id: newId}));
                return;
            }
            
            document.getElementById('confirmModal').style.display = 'flex';
        }
        
        function hideConfirmModal() {
            document.getElementById('confirmModal').style.display = 'none';
        }
        
        function setModbusId() {
            const newId = parseInt(document.getElementById('newId').value);
            const button = document.getElementById('setButton');
            
            hideConfirmModal();
            
            button.disabled = true;
            button.innerHTML = `<span data-i18n="settingId">${t('settingId')}</span> <span class="loader"></span>`;
            
            fetch('/api/set_modbus_id', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    new_id: newId
                })
            })
            .then(response => response.json())
            .then(data => {
                button.disabled = false;
                button.innerHTML = `<span data-i18n="setIdButton">${t('setIdButton')}</span>`;
                
                if (data.success) {
                    showStatus('success', t('successMessage', {id: newId}));
                    // Nach Erfolg erneut scannen
                    setTimeout(scanDevices, 2000);
                } else {
                    showStatus('error', t('errorSettingId') + ' ' + data.error);
                }
            })
            .catch(error => {
                button.disabled = false;
                button.innerHTML = `<span data-i18n="setIdButton">${t('setIdButton')}</span>`;
                showStatus('error', t('errorConnection') + ' ' + error);
            });
        }
        
        function showStatus(type, message) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.style.display = 'block';
        }
        
        // Initial scan beim Laden
        window.addEventListener('load', () => {
            // Gespeicherte Sprache laden (mit beiden Keys für Kompatibilität)
            const savedLang = localStorage.getItem('language') || localStorage.getItem('setupLanguage') || 'de';
            setLanguage(savedLang);
            scanDevices();
        });
        
        function confirmExit(event) {
            event.preventDefault();
            if (confirm(t('confirmExit'))) {
                exitSetupMode();
            }
        }
        
        function exitSetupMode() {
            // Steuerung wieder aktivieren
            fetch('/api/resume_control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', t('controlResuming'));
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                } else {
                    showStatus('error', t('errorSettingId') + ' ' + data.error);
                }
            })
            .catch(error => {
                showStatus('error', t('errorConnection') + ' ' + error);
            });
        }
        
        // Browser-Zurück-Button abfangen
        window.addEventListener('beforeunload', (event) => {
            // Warnung anzeigen
            event.preventDefault();
            event.returnValue = t('exitWarning');
        });
    </script>
</body>
</html>
'''

# HTML-Template für Dashboard (Home Assistant Lovelace Dark Mode Style)
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marstek Energy Dashboard</title>
    <style>
        :root {
            --primary-color: #03a9f4;
            --accent-color: #ff9800;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --error-color: #f44336;
            --info-color: #2196f3;
            
            --bg-primary: #111111;
            --bg-secondary: #1c1c1c;
            --bg-card: #1c1c1c;
            --bg-card-hover: #242424;
            
            --text-primary: #e1e1e1;
            --text-secondary: #9e9e9e;
            --text-disabled: #6e6e6e;
            
            --border-color: #282828;
            --divider-color: #2c2c2c;
            
            --shadow-card: 0 2px 4px 0 rgba(0,0,0,0.5);
            --shadow-card-hover: 0 4px 8px 0 rgba(0,0,0,0.6);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem 0;
            position: relative;
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 400;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .setup-link {
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }
        
        .setup-link:hover {
            background: var(--bg-card-hover);
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .language-switcher {
            position: absolute;
            top: 1.5rem;
            left: 1.5rem;
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .language-button {
            padding: 0.375rem 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.75rem;
        }
        
        .language-button.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        .language-button:hover:not(.active) {
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: var(--shadow-card);
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }
        
        .card:hover {
            box-shadow: var(--shadow-card-hover);
            background: var(--bg-card-hover);
            transform: translateY(-1px);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--divider-color);
        }
        
        .card-icon {
            font-size: 1.5rem;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .card-title {
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-primary);
            flex: 1;
        }
        
        .card-content {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .metric-value {
            font-size: 1.125rem;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .power-display {
            text-align: center;
            padding: 1.5rem 0;
        }
        
        .power-value {
            font-size: 3rem;
            font-weight: 300;
            line-height: 1;
            margin-bottom: 0.5rem;
            transition: color 0.3s ease;
        }
        
        .power-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .power-positive { color: var(--error-color); }
        .power-negative { color: var(--success-color); }
        .power-zero { color: var(--text-secondary); }
        
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 0.75rem;
            border-radius: 16px;
            font-size: 0.875rem;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-ok .status-dot { background: var(--success-color); }
        .status-warning .status-dot { background: var(--warning-color); }
        .status-error .status-dot { background: var(--error-color); }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .battery-grid {
            display: grid;
            gap: 0.75rem;
        }
        
        .battery-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 1rem;
            align-items: center;
            transition: all 0.2s ease;
        }
        
        .battery-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--primary-color);
        }
        
        .battery-icon {
            font-size: 2rem;
        }
        
        .battery-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .battery-name {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .battery-status {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .battery-soc {
            font-size: 1.5rem;
            font-weight: 300;
        }
        
        .soc-high { color: var(--success-color); }
        .soc-medium { color: var(--warning-color); }
        .soc-low { color: var(--error-color); }
        
        .log-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
        }
        
        .log-entry {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 4px;
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            transition: background 0.2s ease;
        }
        
        .log-entry:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .log-time {
            color: var(--text-disabled);
            flex-shrink: 0;
        }
        
        .log-level {
            font-weight: 600;
            text-transform: uppercase;
            flex-shrink: 0;
            width: 60px;
        }
        
        .log-message {
            color: var(--text-primary);
            word-break: break-word;
        }
        
        .log-info .log-level { color: var(--info-color); }
        .log-warning .log-level { color: var(--warning-color); }
        .log-error .log-level { color: var(--error-color); }
        
        .timestamp {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
            padding: 1rem;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-disabled);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .power-value {
                font-size: 2.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="language-switcher">
            <button class="language-button active" onclick="setLanguage('de')" data-lang="de">DE</button>
            <button class="language-button" onclick="setLanguage('en')" data-lang="en">EN</button>
        </div>
        
        <div class="header">
            <h1>⚡ Marstek Energy Dashboard</h1>
            <div class="subtitle" data-i18n="subtitle">Echtzeit Solar & Batterie Monitoring</div>
            <a href="/setup" class="setup-link" title="Modbus ID Setup">
                ⚙️ <span data-i18n="setupButton">Setup</span>
            </a>
            <a href="/config" class="setup-link" style="right: 8rem;" title="Configuration">
                📋 <span data-i18n="configButton">Konfig</span>
            </a>
        </div>
        
        <div class="timestamp" id="timestamp" data-i18n="initializing">Initialisiere...</div>
        
        <div class="dashboard-grid">
            <!-- Grid Power Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">⚡</div>
                    <div class="card-title" data-i18n="gridPowerTitle">Netzleistung</div>
                    <div id="systemStatus" class="status-indicator status-ok">
                        <span class="status-dot"></span>
                        <span>Online</span>
                    </div>
                </div>
                <div class="card-content">
                    <div class="power-display">
                        <div class="power-value" id="gridPower">-- W</div>
                        <div class="power-label" data-i18n="currentDraw">Aktueller Bezug</div>
                    </div>
                </div>
            </div>
            
            <!-- Batteries Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">🔋</div>
                    <div class="card-title" data-i18n="batteryStorageTitle">Batteriespeicher</div>
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label" data-i18n="totalPower">Gesamtleistung</span>
                        <span class="metric-value" id="batteryPower">-- W</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label" data-i18n="mode">Modus</span>
                        <span class="metric-value" id="batteryMode">--</span>
                    </div>
                    <div class="battery-grid" id="batteryDetails">
                        <!-- Battery items will be inserted here -->
                    </div>
                </div>
            </div>
            
            <!-- Energy Meter Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <div class="card-title" data-i18n="energyMeterTitle">Energiemessgerät</div>
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label" data-i18n="type">Typ</span>
                        <span class="metric-value" id="meterType">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label" data-i18n="status">Status</span>
                        <span class="metric-value" id="meterStatus">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label" data-i18n="errors">Fehler</span>
                        <span class="metric-value" id="meterErrors">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label" data-i18n="lastSuccess">Letzter Erfolg</span>
                        <span class="metric-value" id="meterLastSuccess">--</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Log Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon">📝</div>
                <div class="card-title" data-i18n="systemLogTitle">System-Log</div>
            </div>
            <div class="log-container" id="logContainer">
                <!-- Log entries will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        let updateInterval;
        let currentLanguage = 'de';
        
        // Übersetzungen
        const translations = {
            de: {
                subtitle: 'Echtzeit Solar & Batterie Monitoring',
                setupButton: 'Setup',
                configButton: 'Konfig',
                initializing: 'Initialisiere...',
                lastUpdate: 'Letzte Aktualisierung',
                gridPowerTitle: 'Netzleistung',
                currentDraw: 'Aktueller Bezug',
                currentFeed: 'Aktuelle Einspeisung',
                batteryStorageTitle: 'Batteriespeicher',
                totalPower: 'Gesamtleistung',
                mode: 'Modus',
                battery: 'Batterie',
                energyMeterTitle: 'Energiemessgerät',
                type: 'Typ',
                status: 'Status',
                errors: 'Fehler',
                lastSuccess: 'Letzter Erfolg',
                systemLogTitle: 'System-Log',
                online: 'Online',
                offline: 'Offline',
                connectionError: 'Verbindungsfehler',
                controlDisabled: 'Steuerung deaktiviert (Setup-Modus)',
                stop: 'Stopp',
                charging: 'Laden',
                discharging: 'Entladen',
                unknown: 'Unbekannt',
                seconds: 's'
            },
            en: {
                subtitle: 'Real-time Solar & Battery Monitoring',
                setupButton: 'Setup',
                initializing: 'Initializing...',
                lastUpdate: 'Last Update',
                gridPowerTitle: 'Grid Power',
                currentDraw: 'Current Draw',
                currentFeed: 'Current Feed-in',
                batteryStorageTitle: 'Battery Storage',
                totalPower: 'Total Power',
                mode: 'Mode',
                battery: 'Battery',
                energyMeterTitle: 'Energy Meter',
                type: 'Type',
                status: 'Status',
                errors: 'Errors',
                lastSuccess: 'Last Success',
                systemLogTitle: 'System Log',
                online: 'Online',
                offline: 'Offline',
                connectionError: 'Connection Error',
                controlDisabled: 'Control disabled (Setup mode)',
                stop: 'Stop',
                charging: 'Charging',
                discharging: 'Discharging',
                unknown: 'Unknown',
                seconds: 's'
            }
        };
        
        // Sprache setzen
        function setLanguage(lang) {
            currentLanguage = lang;
            
            // Buttons aktualisieren
            document.querySelectorAll('.language-button').forEach(btn => {
                if (btn.dataset.lang === lang) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Übersetzungen anwenden
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                if (translations[lang][key]) {
                    element.textContent = translations[lang][key];
                }
            });
            
            // Netzleistung Label aktualisieren falls nötig
            const gridPowerEl = document.getElementById('gridPower');
            if (gridPowerEl) {
                const gridPowerText = gridPowerEl.textContent;
                const gridPower = parseFloat(gridPowerText);
                if (!isNaN(gridPower)) {
                    const powerLabel = document.querySelector('.power-label');
                    if (powerLabel) {
                        powerLabel.textContent = gridPower < 0 ? t('currentFeed') : t('currentDraw');
                    }
                }
            }
            
            // localStorage speichern
            localStorage.setItem('language', lang);
        }
        
        // Hilfsfunktion für Übersetzungen
        function t(key) {
            return translations[currentLanguage][key] || key;
        }
        
        function formatPower(power) {
            if (power === null || power === undefined) return '-- W';
            return Math.round(power) + ' W';
        }
        
        function getPowerClass(power) {
            if (power > 0) return 'power-positive';
            if (power < 0) return 'power-negative';
            return 'power-zero';
        }
        
        function getStatusClass(status) {
            if (status === 'ok') return 'status-ok';
            if (status === 'warning') return 'status-warning';
            if (status === 'error') return 'status-error';
            return '';
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('timestamp').textContent = 
                        t('lastUpdate') + ': ' + new Date(data.timestamp).toLocaleTimeString();
                    
                    const gridPower = data.grid_power;
                    document.getElementById('gridPower').textContent = formatPower(gridPower);
                    document.getElementById('gridPower').className = 'power-value ' + getPowerClass(gridPower);
                    
                    // Power Label dynamisch aktualisieren
                    const powerLabel = document.querySelector('.power-label');
                    if (powerLabel) {
                        powerLabel.textContent = gridPower < 0 ? t('currentFeed') : t('currentDraw');
                    }
                    
                    const sysStatus = data.system_status;
                    const statusEl = document.getElementById('systemStatus');
                    
                    // Prüfe ob Steuerung deaktiviert ist
                    if (data.controller && !data.controller.enabled) {
                        statusEl.className = 'status-indicator status-warning';
                        statusEl.innerHTML = `
                            <span class="status-dot"></span>
                            <span>${t('controlDisabled')}</span>
                        `;
                    } else {
                        statusEl.className = 'status-indicator ' + getStatusClass(sysStatus.status);
                        statusEl.innerHTML = `
                            <span class="status-dot"></span>
                            <span>${sysStatus.message}</span>
                        `;
                    }
                    
                    const batteryPower = data.battery_power;
                    document.getElementById('batteryPower').textContent = formatPower(batteryPower);
                    document.getElementById('batteryPower').className = 'metric-value ' + getPowerClass(batteryPower);
                    
                    // Modus übersetzen
                    const modeText = data.controller.mode_text;
                    const modeTranslations = {
                        'Stopp': t('stop'),
                        'Laden': t('charging'),
                        'Entladen': t('discharging')
                    };
                    document.getElementById('batteryMode').textContent = modeTranslations[modeText] || modeText;
                    
                    let batteryHtml = '';
                    for (const [id, battery] of Object.entries(data.batteries)) {
                        let socClass, icon;
                        if (battery.soc === null || battery.soc === undefined) {
                            socClass = 'soc-low';
                            icon = '🔋';
                        } else {
                            if (battery.soc > 60) {
                                socClass = 'soc-high';
                                icon = '🔋';
                            } else if (battery.soc > 30) {
                                socClass = 'soc-medium';
                                icon = '🔋';
                            } else {
                                socClass = 'soc-low';
                                icon = '🪫';
                            }
                        }
                        
                        const batteryModeTranslations = {
                            'Stopp': t('stop'),
                            'Laden': t('charging'),
                            'Entladen': t('discharging'),
                            'Unbekannt': t('unknown')
                        };
                        
                        batteryHtml += `
                            <div class="battery-item">
                                <div class="battery-icon">${icon}</div>
                                <div class="battery-info">
                                    <div class="battery-name">${t('battery')} ${id}</div>
                                    <div class="battery-status">${battery.current_power}W | ${batteryModeTranslations[battery.mode_text] || battery.mode_text}</div>
                                </div>
                                <div class="battery-soc ${socClass}">
                                    ${battery.soc !== null ? battery.soc.toFixed(0) + '%' : '--'}
                                </div>
                            </div>
                        `;
                    }
                    document.getElementById('batteryDetails').innerHTML = batteryHtml;
                    
                    document.getElementById('meterType').textContent = data.meter_type.toUpperCase();
                    document.getElementById('meterStatus').textContent = data.energy_meter.online ? t('online') : t('offline');
                    document.getElementById('meterStatus').className = 'metric-value ' + 
                        (data.energy_meter.online ? 'status-ok' : 'status-error');
                    document.getElementById('meterErrors').textContent = data.energy_meter.failure_count;
                    document.getElementById('meterLastSuccess').textContent = data.energy_meter.seconds_since_success + t('seconds');
                })
                .catch(error => {
                    console.error('Status update error:', error);
                    document.getElementById('timestamp').textContent = t('connectionError') + ': ' + new Date().toLocaleTimeString();
                });
        }
        
        function updateLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('logContainer');
                    container.innerHTML = '';
                    
                    data.logs.forEach(log => {
                        const div = document.createElement('div');
                        div.className = 'log-entry log-' + log.level.toLowerCase();
                        div.innerHTML = `
                            <span class="log-time">${log.timestamp}</span>
                            <span class="log-level">${log.level}</span>
                            <span class="log-message">${log.message}</span>
                        `;
                        container.appendChild(div);
                    });
                    
                    container.scrollTop = container.scrollHeight;
                })
                .catch(error => console.error('Log update error:', error));
        }
        
        // Initialisierung
        window.addEventListener('load', () => {
            // Gespeicherte Sprache laden (mit Fallback zu setup-spezifischer Einstellung)
            const savedLang = localStorage.getItem('language') || localStorage.getItem('setupLanguage') || 'de';
            setLanguage(savedLang);
            
            // Initiale Updates
            updateStatus();
            updateLogs();
            updateInterval = setInterval(() => {
                updateStatus();
                updateLogs();
            }, 2000);
        });
        
        // Cleanup on page exit
        window.addEventListener('beforeunload', () => {
            if (updateInterval) clearInterval(updateInterval);
        });
    </script>
</body>
</html>
'''
