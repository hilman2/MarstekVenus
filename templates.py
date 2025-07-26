"""
HTML Templates für die Web-Oberfläche
"""

# HTML-Template für Setup-Seite
SETUP_HTML = '''
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
        }
        
        .setup-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
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
        
        .warning-card {
            background: rgba(255, 152, 0, 0.1);
            border: 1px solid var(--warning-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        
        .warning-card h3 {
            color: var(--warning-color);
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .warning-card p {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin: 0;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        
        .card-header h2 {
            font-size: 1.25rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--primary-color);
        }
        
        .button {
            padding: 0.75rem 1.5rem;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .button:hover {
            background: #0288d1;
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .button-success {
            background: var(--success-color);
        }
        
        .button-success:hover {
            background: #388e3c;
        }
        
        .button-danger {
            background: var(--error-color);
        }
        
        .button-danger:hover {
            background: #d32f2f;
        }
        
        .device-list {
            margin-top: 1rem;
        }
        
        .device-item {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s ease;
        }
        
        .device-item:hover {
            background: var(--bg-card-hover);
            border-color: var(--primary-color);
        }
        
        .device-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .device-icon {
            font-size: 2rem;
        }
        
        .device-details h3 {
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .device-details p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin: 0;
        }
        
        .loader {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s linear infinite;
            margin-left: 0.5rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
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
        
        .status-info {
            background: rgba(3, 169, 244, 0.1);
            border: 1px solid var(--primary-color);
            color: var(--primary-color);
        }
        
        .log-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            display: flex;
            gap: 1rem;
        }
        
        .log-time {
            color: var(--text-disabled);
        }
        
        .log-level {
            font-weight: 500;
            min-width: 60px;
        }
        
        .log-level.log-info {
            color: var(--primary-color);
        }
        
        .log-level.log-warning {
            color: var(--warning-color);
        }
        
        .log-level.log-error {
            color: var(--error-color);
        }
        
        .log-message {
            color: var(--text-primary);
        }
    </style>
</head>
<body>
    <div class="setup-container">
        <div class="header">
            <div class="language-switcher">
                <button class="language-button active" onclick="setLanguage('de')" data-lang="de">DE</button>
                <button class="language-button" onclick="setLanguage('en')" data-lang="en">EN</button>
            </div>
            <h1>🔧 <span data-i18n="title">Marstek Modbus ID Setup</span></h1>
            <p data-i18n="subtitle">Konfiguration der Modbus Slave IDs für Marstek Batteriespeicher</p>
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
        
        <div class="warning-card">
            <h3>⚠️ <span data-i18n="warningTitle">Wichtiger Hinweis</span></h3>
            <p data-i18n="warningText">Die Akku-Steuerung ist während des Setup-Modus deaktiviert. Nach Abschluss der Konfiguration wird die Steuerung automatisch wieder aktiviert.</p>
        </div>
        
        <!-- Scan-Bereich -->
        <div class="card">
            <div class="card-header">
                <h2>🔍 <span data-i18n="scanTitle">Geräte-Scan</span></h2>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="scanIp" data-i18n="ipLabel">IP-Adresse</label>
                    <input type="text" id="scanIp" placeholder="Wird aus config.json geladen...">
                </div>
                <div class="form-group">
                    <label for="scanPort" data-i18n="portLabel">Port</label>
                    <input type="number" id="scanPort" placeholder="502" min="1" max="65535">
                </div>
            </div>
            
            <button class="button" onclick="scanDevices()" id="scanButton">
                <span data-i18n="scanButton">Nach Geräten suchen</span>
            </button>
            
            <div id="scanResults" class="device-list" style="display: none;">
                <h3 data-i18n="foundDevices">Gefundene Geräte:</h3>
                <div id="deviceList"></div>
            </div>
        </div>
        
        <!-- ID-Änderung -->
        <div class="card">
            <div class="card-header">
                <h2>✏️ <span data-i18n="changeIdTitle">Modbus ID ändern</span></h2>
            </div>
            
            <p data-i18n="changeIdInfo" style="color: var(--text-secondary); margin-bottom: 1rem;">
                Verbinden Sie nur den Akku, dessen ID Sie ändern möchten. Alle Akkus hören standardmäßig auf ID 1.
            </p>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="newId" data-i18n="newIdLabel">Neue Modbus ID</label>
                    <input type="number" id="newId" min="1" max="255" placeholder="1-255">
                </div>
            </div>
            
            <button class="button button-success" onclick="setModbusId()" id="setIdButton">
                <span data-i18n="setIdButton">ID setzen</span>
            </button>
        </div>
        
        <!-- Logs -->
        <div class="card">
            <div class="card-header">
                <h2>📋 <span data-i18n="logsTitle">Logs</span></h2>
            </div>
            
            <div class="log-container" id="logContainer">
                <!-- Logs werden hier eingefügt -->
            </div>
        </div>
        
        <!-- Steuerung fortsetzen -->
        <div class="card" style="text-align: center;">
            <h3 data-i18n="resumeTitle">Setup abgeschlossen?</h3>
            <p data-i18n="resumeText" style="color: var(--text-secondary); margin-bottom: 1rem;">
                Aktivieren Sie die Akku-Steuerung wieder, wenn alle IDs konfiguriert sind.
            </p>
            <button class="button button-success" onclick="resumeControl()">
                <span data-i18n="resumeButton">Steuerung aktivieren</span>
            </button>
        </div>
    </div>
    
    <script>
        let currentLanguage = 'de';
        let updateInterval = null;
        
        // Übersetzungen
        const translations = {
            de: {
                title: 'Marstek Modbus ID Setup',
                subtitle: 'Konfiguration der Modbus Slave IDs für Marstek Batteriespeicher',
                backToDashboard: 'Zurück zum Dashboard',
                toSetup: 'Zum Setup',
                toConfig: 'Zur Konfiguration',
                warningTitle: 'Wichtiger Hinweis',
                warningText: 'Die Akku-Steuerung ist während des Setup-Modus deaktiviert. Nach Abschluss der Konfiguration wird die Steuerung automatisch wieder aktiviert.',
                scanTitle: 'Geräte-Scan',
                ipLabel: 'IP-Adresse',
                portLabel: 'Port',
                scanButton: 'Nach Geräten suchen',
                scanning: 'Suche läuft...',
                foundDevices: 'Gefundene Geräte:',
                changeIdTitle: 'Modbus ID ändern',
                changeIdInfo: 'Verbinden Sie nur den Akku, dessen ID Sie ändern möchten. Alle Akkus hören standardmäßig auf ID 1.',
                newIdLabel: 'Neue Modbus ID',
                setIdButton: 'ID setzen',
                settingId: 'Setze ID...',
                logsTitle: 'Logs',
                resumeTitle: 'Setup abgeschlossen?',
                resumeText: 'Aktivieren Sie die Akku-Steuerung wieder, wenn alle IDs konfiguriert sind.',
                resumeButton: 'Steuerung aktivieren',
                noDevicesFound: 'Keine Geräte gefunden',
                deviceFound: 'Gerät auf ID',
                currentId: 'Aktuelle ID',
                errorScanning: 'Fehler beim Scannen',
                errorSettingId: 'Fehler beim Setzen der ID',
                successIdSet: 'ID erfolgreich gesetzt',
                controlResumed: 'Steuerung aktiviert'
            },
            en: {
                title: 'Marstek Modbus ID Setup',
                subtitle: 'Configuration of Modbus Slave IDs for Marstek Battery Storage',
                backToDashboard: 'Back to Dashboard',
                toSetup: 'To Setup',
                toConfig: 'To Configuration',
                warningTitle: 'Important Notice',
                warningText: 'Battery control is disabled during setup mode. Control will be automatically reactivated after configuration is complete.',
                scanTitle: 'Device Scan',
                ipLabel: 'IP Address',
                portLabel: 'Port',
                scanButton: 'Scan for devices',
                scanning: 'Scanning...',
                foundDevices: 'Found devices:',
                changeIdTitle: 'Change Modbus ID',
                changeIdInfo: 'Only connect the battery whose ID you want to change. All batteries listen to ID 1 by default.',
                newIdLabel: 'New Modbus ID',
                setIdButton: 'Set ID',
                settingId: 'Setting ID...',
                logsTitle: 'Logs',
                resumeTitle: 'Setup complete?',
                resumeText: 'Reactivate battery control when all IDs are configured.',
                resumeButton: 'Activate control',
                noDevicesFound: 'No devices found',
                deviceFound: 'Device on ID',
                currentId: 'Current ID',
                errorScanning: 'Error scanning',
                errorSettingId: 'Error setting ID',
                successIdSet: 'ID successfully set',
                controlResumed: 'Control activated'
            }
        };
        
        // Sprache setzen
        function setLanguage(lang) {
            currentLanguage = lang;
            localStorage.setItem('setupLanguage', lang);
            
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
        }
        
        // Hilfsfunktion für Übersetzungen
        function t(key) {
            return translations[currentLanguage][key] || key;
        }
        
        function showStatus(type, message, persistent = false) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.style.display = 'block';
            
            if (!persistent && type === 'success') {
                setTimeout(() => {
                    statusEl.style.display = 'none';
                }, 5000);
            }
        }
        
        function scanDevices() {
            const button = document.getElementById('scanButton');
            const originalText = button.innerHTML;
            button.innerHTML = `<span>${t('scanning')}</span><span class="loader"></span>`;
            button.disabled = true;
            
            const ip = document.getElementById('scanIp').value;
            const port = document.getElementById('scanPort').value;
            
            fetch('/api/scan_modbus_ids', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ip, port: parseInt(port) })
            })
            .then(response => response.json())
            .then(data => {
                button.innerHTML = originalText;
                button.disabled = false;
                
                if (data.success) {
                    displayScanResults(data.found_ids);
                } else {
                    showStatus('error', t('errorScanning') + ': ' + data.error);
                }
            })
            .catch(error => {
                button.innerHTML = originalText;
                button.disabled = false;
                showStatus('error', t('errorScanning') + ': ' + error);
            });
        }
        
        function displayScanResults(devices) {
            const resultsDiv = document.getElementById('scanResults');
            const deviceList = document.getElementById('deviceList');
            
            resultsDiv.style.display = 'block';
            deviceList.innerHTML = '';
            
            if (devices.length === 0) {
                deviceList.innerHTML = `<p style="color: var(--text-secondary);">${t('noDevicesFound')}</p>`;
                return;
            }
            
            devices.forEach(device => {
                const deviceItem = document.createElement('div');
                deviceItem.className = 'device-item';
                deviceItem.innerHTML = `
                    <div class="device-info">
                        <div class="device-icon">🔋</div>
                        <div class="device-details">
                            <h3>${t('deviceFound')} ${device.id}</h3>
                            <p>${t('currentId')}: ${device.current_id}</p>
                        </div>
                    </div>
                `;
                deviceList.appendChild(deviceItem);
            });
        }
        
        function setModbusId() {
            const newId = document.getElementById('newId').value;
            
            if (!newId || newId < 1 || newId > 255) {
                showStatus('error', 'Bitte geben Sie eine gültige ID zwischen 1 und 255 ein');
                return;
            }
            
            const button = document.getElementById('setIdButton');
            const originalText = button.innerHTML;
            button.innerHTML = `<span>${t('settingId')}</span><span class="loader"></span>`;
            button.disabled = true;
            
            const ip = document.getElementById('scanIp').value;
            const port = document.getElementById('scanPort').value;
            
            fetch('/api/set_modbus_id', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    new_id: parseInt(newId),
                    ip: ip,
                    port: parseInt(port)
                })
            })
            .then(response => response.json())
            .then(data => {
                button.innerHTML = originalText;
                button.disabled = false;
                
                if (data.success) {
                    showStatus('success', t('successIdSet') + ': ' + data.message);
                    document.getElementById('newId').value = '';
                } else {
                    showStatus('error', t('errorSettingId') + ': ' + data.error);
                }
            })
            .catch(error => {
                button.innerHTML = originalText;
                button.disabled = false;
                showStatus('error', t('errorSettingId') + ': ' + error);
            });
        }
        
        function resumeControl() {
            fetch('/api/resume_control', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', t('controlResumed'));
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                } else {
                    showStatus('error', data.error);
                }
            })
            .catch(error => {
                showStatus('error', error);
            });
        }
        
        function loadBatteryConfig() {
            // IP und Port aus Battery-Config laden (nur beim ersten Laden)
            fetch('/api/get_battery_config')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const ipField = document.getElementById('scanIp');
                        const portField = document.getElementById('scanPort');
                        
                        // Nur setzen, wenn Felder leer sind
                        if (data.ip && !ipField.value) {
                            ipField.value = data.ip;
                            ipField.placeholder = 'Aus config.json geladen';
                        }
                        if (data.port && !portField.value) {
                            portField.value = data.port;
                        }
                    } else {
                        console.warn('Konnte Battery-Config nicht laden:', data.error);
                    }
                })
                .catch(error => console.error('Config load error:', error));
        }
        
        function updateStatus() {
            // Diese Funktion bleibt für andere Status-Updates
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
            
            // Battery-Config einmalig laden
            loadBatteryConfig();
            
            // Initiale Updates
            updateLogs();
            updateInterval = setInterval(() => {
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
