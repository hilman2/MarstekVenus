# CONFIG_HTML Template für web_server.py

CONFIG_HTML_TEMPLATE = '''
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
