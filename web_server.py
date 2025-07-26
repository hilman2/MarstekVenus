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

# HTML-Template für Dashboard (Home Assistant Lovelace Dark Mode Style)
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="de">
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
        <div class="header">
            <h1>⚡ Marstek Energy Dashboard</h1>
            <div class="subtitle">Real-time Solar & Battery Monitoring</div>
        </div>
        
        <div class="timestamp" id="timestamp">Initializing...</div>
        
        <div class="dashboard-grid">
            <!-- Grid Power Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">⚡</div>
                    <div class="card-title">Grid Power</div>
                    <div id="systemStatus" class="status-indicator status-ok">
                        <span class="status-dot"></span>
                        <span>Online</span>
                    </div>
                </div>
                <div class="card-content">
                    <div class="power-display">
                        <div class="power-value" id="gridPower">-- W</div>
                        <div class="power-label">Current Draw</div>
                    </div>
                </div>
            </div>
            
            <!-- Batteries Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">🔋</div>
                    <div class="card-title">Battery Storage</div>
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Total Power</span>
                        <span class="metric-value" id="batteryPower">-- W</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Mode</span>
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
                    <div class="card-title">Energy Meter</div>
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Type</span>
                        <span class="metric-value" id="meterType">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Status</span>
                        <span class="metric-value" id="meterStatus">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Errors</span>
                        <span class="metric-value" id="meterErrors">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Last Success</span>
                        <span class="metric-value" id="meterLastSuccess">--</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Log Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon">📝</div>
                <div class="card-title">System Log</div>
            </div>
            <div class="log-container" id="logContainer">
                <!-- Log entries will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        let updateInterval;
        
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
                        'Last Update: ' + new Date(data.timestamp).toLocaleTimeString();
                    
                    const gridPower = data.grid_power;
                    document.getElementById('gridPower').textContent = formatPower(gridPower);
                    document.getElementById('gridPower').className = 'power-value ' + getPowerClass(gridPower);
                    
                    const sysStatus = data.system_status;
                    const statusEl = document.getElementById('systemStatus');
                    statusEl.className = 'status-indicator ' + getStatusClass(sysStatus.status);
                    statusEl.innerHTML = `
                        <span class="status-dot"></span>
                        <span>${sysStatus.message}</span>
                    `;
                    
                    const batteryPower = data.battery_power;
                    document.getElementById('batteryPower').textContent = formatPower(batteryPower);
                    document.getElementById('batteryPower').className = 'metric-value ' + getPowerClass(batteryPower);
                    
                    document.getElementById('batteryMode').textContent = data.controller.mode_text;
                    
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
                        
                        batteryHtml += `
                            <div class="battery-item">
                                <div class="battery-icon">${icon}</div>
                                <div class="battery-info">
                                    <div class="battery-name">Battery ${id}</div>
                                    <div class="battery-status">${battery.current_power}W | ${battery.mode_text}</div>
                                </div>
                                <div class="battery-soc ${socClass}">
                                    ${battery.soc !== null ? battery.soc.toFixed(0) + '%' : '--'}
                                </div>
                            </div>
                        `;
                    }
                    document.getElementById('batteryDetails').innerHTML = batteryHtml;
                    
                    document.getElementById('meterType').textContent = data.meter_type.toUpperCase();
                    document.getElementById('meterStatus').textContent = data.energy_meter.online ? 'Online' : 'Offline';
                    document.getElementById('meterStatus').className = 'metric-value ' + 
                        (data.energy_meter.online ? 'status-ok' : 'status-error');
                    document.getElementById('meterErrors').textContent = data.energy_meter.failure_count;
                    document.getElementById('meterLastSuccess').textContent = data.energy_meter.seconds_since_success + 's';
                })
                .catch(error => {
                    console.error('Status update error:', error);
                    document.getElementById('timestamp').textContent = 'Connection Error: ' + new Date().toLocaleTimeString();
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
        
        // Auto-update every 2 seconds
        updateStatus();
        updateLogs();
        updateInterval = setInterval(() => {
            updateStatus();
            updateLogs();
        }, 2000);
        
        // Cleanup on page exit
        window.addEventListener('beforeunload', () => {
            if (updateInterval) clearInterval(updateInterval);
        });
    </script>
</body>
</html>
'''
