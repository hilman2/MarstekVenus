# Marstek PV-Akku Steuerung

Ein intelligentes Energiemanagement-System zur Nulleinspeisung (Zero-Feed) für PV-Anlagen mit Marstek/Duravolt Batteriespeichern.
![Dashboard](https://github.com/user-attachments/assets/d421fa86-fb10-4c82-a589-f77c970c2cc4)

![setup](https://github.com/user-attachments/assets/3a6e9325-7a52-4edf-a679-a42810f3659d)

## 🎯 Hauptfunktionen

- **Nulleinspeisung (Zero-Feed)**: Automatische Regelung der Akkuleistung zur Vermeidung von Netzeinspeisung
- **Echtzeit-Monitoring**: Web-basiertes Dashboard mit Live-Daten
- **Multi-Akku-Support**: Verwaltung mehrerer Batteriespeicher gleichzeitig
- **Intelligente Lastverteilung**: Automatische Verteilung der Leistung auf verfügbare Akkus
- **Flexible Energiemessung**: Unterstützung für Shelly 3EM Pro und EcoTracker
- **Modbus-TCP Kommunikation**: Direkte Steuerung der Marstek/Duravolt Akkus
- **Durchschnittsbildung**: Stabilere Regelung durch 3-Werte-Durchschnitt der Energiemessungen
- **Modbus ID Setup**: Web-basierte Konfiguration neuer Akkus mit automatischer ID-Vergabe

## 📋 Systemanforderungen

- Python 3.8 oder höher
- Netzwerkzugriff auf Energiemessgerät (Shelly 3EM Pro oder EcoTracker) und Marstek/Duravolt Akkus
- Linux (Debian/Ubuntu) oder Windows
- Ca. 50 MB freier Speicherplatz

## 🏗️ Systemarchitektur

### Komponenten

1. **main.py**: Hauptanwendung mit Steuerungslogik
2. **shelly_client.py**: Shelly 3EM Pro Kommunikation
3. **ecotracker_client.py**: EcoTracker Kommunikation
4. **battery_client.py**: Marstek/Duravolt Modbus-Client
5. **zero_feed_control.py**: Nulleinspeisungs-Regelungslogik
6. **web_server.py**: Web-Dashboard für Monitoring
7. **config_loader.py**: Konfigurationsverwaltung
8. **config.json**: Zentrale Konfigurationsdatei

### Kommunikationsfluss

```
Energiemessgerät (HTTP) → Steuerung → Marstek Akkus (Modbus TCP)
(Shelly/EcoTracker)          ↓              ↓
        ↓               Regellogik    Lade/Entlade
   Netzmessung              ↓              ↓
        ↓               Statusdaten         ↓
    Web-Dashboard ←-----------------------← Systemstatus
```

## 🚀 Installation

### Linux (Debian/Ubuntu)

#### 1. System vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Python und pip installieren
sudo apt install python3 python3-pip python3-venv git -y

# Projektverzeichnis erstellen
sudo mkdir -p /opt/marstek
sudo chown $USER:$USER /opt/marstek
cd /opt/marstek

# Projekt klonen oder Dateien kopieren
# git clone <repository-url> .
# ODER
# Dateien manuell nach /opt/marstek kopieren
```

#### 2. Virtuelle Umgebung erstellen

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate
```

#### 3. Abhängigkeiten installieren

```bash
# Requirements installieren
pip install -r requirements.txt
```

#### 4. Konfiguration anpassen

```bash
# Kopiere Beispielkonfiguration
cp config.example.json config.json

# Bearbeite die Konfiguration
nano config.json
```

Wichtige Konfigurationsparameter:
- `energy_meter.type`: Typ des Energiemessgeräts ('shelly' oder 'ecotracker')
- `shelly.ip`: IP-Adresse des Shelly 3EM Pro (wenn verwendet)
- `ecotracker.ip`: IP-Adresse des EcoTrackers (wenn verwendet)
- `battery.ip`: IP-Adresse der Marstek Akkus
- `battery.akku_ids`: Liste der Akku-IDs (z.B. [2] oder [1, 2])
- `web.port`: Port für Web-Dashboard (Standard: 8080)

#### 5. Systemd-Service einrichten

Erstelle die Service-Datei:

```bash
sudo nano /etc/systemd/system/marstek.service
```

Inhalt der marstek.service:

```ini
[Unit]
Description=Marstek PV-Akku Steuerung
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/marstek
Environment="PATH=/opt/marstek/venv/bin"
ExecStart=/opt/marstek/venv/bin/python /opt/marstek/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/marstek.log
StandardError=append:/var/log/marstek.error.log

[Install]
WantedBy=multi-user.target
```

Service aktivieren:

```bash
# Service laden
sudo systemctl daemon-reload

# Service aktivieren (Autostart)
sudo systemctl enable marstek.service

# Service starten
sudo systemctl start marstek.service

# Status prüfen
sudo systemctl status marstek.service
```

### Windows Installation

#### 1. Automatische Installation mit install.bat

Führe die `install.bat` Datei als Administrator aus. Diese wird:
- Python-Abhängigkeiten installieren
- Eine Beispielkonfiguration erstellen
- Das System starten

#### 2. Manuelle Installation

```cmd
# Python-Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration kopieren und anpassen
copy config.example.json config.json
notepad config.json

# System starten
python main.py
```

## 📖 Konfiguration

### config.json Struktur

```json
{
  "energy_meter": {
    "type": "shelly",               // 'shelly' oder 'ecotracker'
    "comment": "Verfügbare Typen: 'shelly' oder 'ecotracker'"
  },
  
  "shelly": {
    "ip": "192.168.1.100",          // Shelly 3EM Pro IP
    "timeout_seconds": 5,           // Verbindungs-Timeout
    "max_failures_before_stop": 2   // Max. Fehler vor Akku-Stopp
  },
  
  "ecotracker": {
    "ip": "192.168.1.101",          // EcoTracker IP
    "timeout_seconds": 5,           // Verbindungs-Timeout
    "max_failures_before_stop": 2   // Max. Fehler vor Akku-Stopp
  },
  
  "battery": {
    "ip": "192.168.1.200",          // Marstek Gateway IP
    "port": 502,                    // Modbus TCP Port
    "akku_ids": [1, 2],            // Liste der Akku-IDs
    "max_power_per_battery": 2500,  // Max. Leistung pro Akku (W)
    "min_power_per_battery": 50,    // Min. Leistung pro Akku (W)
    "min_soc_for_discharge": 11,    // Min. SoC für Entladung (%)
    "max_soc_for_charge": 98        // Max. SoC für Ladung (%)
  },
  
  "control": {
    "poll_interval_seconds": 2,        // Regelungsintervall
    "soc_update_interval_seconds": 30, // SoC-Update Intervall
    "target_grid_power_charge": -20,   // Ziel-Netzleistung Laden (W)
    "target_grid_power_discharge": 20  // Ziel-Netzleistung Entladen (W)
  },
  
  "web": {
    "host": "0.0.0.0",              // Web-Server IP (0.0.0.0 = alle)
    "port": 8080                    // Web-Server Port
  }
}
```

## 🖥️ Bedienung

### Web-Dashboard

Nach dem Start ist das Web-Dashboard erreichbar unter:
- **Lokal**: http://localhost:8080
- **Netzwerk**: http://<server-ip>:8080

Das Dashboard zeigt:
- Aktuelle Netzleistung (Energiemessgerät)
- Typ des verwendeten Energiemessgeräts
- Akku-Status (SoC, Leistung, Modus)
- Systemstatus und Fehler
- Live-Log der letzten Ereignisse

### Modbus ID Setup

Neue Akkus können über die Setup-Seite konfiguriert werden:

1. **Setup-Seite öffnen**: Klicken Sie auf den "Setup" Button im Dashboard oder navigieren Sie zu http://<server-ip>:8080/setup
   - **⚠️ WICHTIG**: Die Akku-Steuerung wird automatisch gestoppt beim Betreten des Setup-Modus
   - Das Dashboard zeigt "Steuerung deaktiviert (Setup-Modus)" an

2. **Vorhandene Geräte scannen**: 
   - Klicken Sie auf "Geräte scannen"
   - Das System prüft die IDs 1-10 und zeigt gefundene Geräte an
   - Automatisch wird die nächste freie ID vorgeschlagen

3. **Neue ID vergeben**:
   - **WICHTIG**: Es darf nur EIN neuer Akku mit ID 1 angeschlossen sein!
   - Trennen Sie alle anderen neuen Akkus vor dem Setzen der ID
   - Wählen Sie die neue ID (1-255)
   - Klicken Sie auf "ID 1 → neue ID setzen"
   - Bestätigen Sie die Sicherheitsabfrage

4. **Setup-Modus beenden**:
   - Klicken Sie auf "🏁 Setup-Modus beenden und Steuerung fortsetzen"
   - Oder nutzen Sie den "Zurück zum Dashboard" Link
   - Die Akku-Steuerung wird automatisch wieder aktiviert

5. **Konfiguration aktualisieren**:
   - Nach erfolgreichem Setzen der ID muss die neue ID in der `config.json` unter `battery.akku_ids` eingetragen werden
   - Starten Sie das System neu, damit die Änderungen wirksam werden

**Sicherheitsfunktionen**:
- Die Akku-Steuerung wird automatisch gestoppt beim Betreten des Setup-Modus
- Eine Warnung wird angezeigt, dass die Steuerung deaktiviert ist
- Beim Verlassen der Seite erfolgt eine Sicherheitsabfrage
- Die Steuerung kann jederzeit wieder aktiviert werden

**Hintergrund**: Alle Marstek/Duravolt Akkus werden vom Hersteller mit der Modbus Slave ID 1 ausgeliefert. Um mehrere Akkus gleichzeitig zu betreiben, muss jeder Akku eine eindeutige ID erhalten.

### Systemd-Befehle (Linux)

```bash
# Status anzeigen
sudo systemctl status marstek

# Stoppen
sudo systemctl stop marstek

# Starten
sudo systemctl start marstek

# Neustart
sudo systemctl restart marstek

# Logs anzeigen
sudo journalctl -u marstek -f

# Deaktivieren (kein Autostart)
sudo systemctl disable marstek
```

## 🔧 Wartung

### Log-Dateien

- **Linux Service**: `/var/log/marstek.log` und `/var/log/marstek.error.log`
- **Manueller Start**: `logs/marstek.log` im Projektverzeichnis

### Backup

Wichtige Dateien für Backup:
- `config.json` - Ihre Konfiguration
- `logs/` - Log-Dateien (optional)

### Updates

```bash
# Service stoppen
sudo systemctl stop marstek

# Ins Verzeichnis wechseln
cd /opt/marstek

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Code aktualisieren
git pull
# ODER neue Dateien manuell kopieren

# Abhängigkeiten aktualisieren
pip install -r requirements.txt --upgrade

# Service starten
sudo systemctl start marstek
```

## 🚨 Fehlerbehebung

### Häufige Probleme

1. **Energiemessgerät nicht erreichbar**
   - IP-Adresse in config.json prüfen (shelly.ip oder ecotracker.ip)
   - Richtigen Typ in energy_meter.type konfiguriert?
   - Netzwerkverbindung testen: `ping <ip-adresse>`
   - Firewall-Einstellungen prüfen

2. **Akkus reagieren nicht**
   - Modbus-Gateway IP prüfen
   - Port 502 muss erreichbar sein
   - Akku-IDs in config.json prüfen

3. **Web-Dashboard nicht erreichbar**
   - Port 8080 in Firewall freigeben
   - Andere Anwendung auf Port 8080? → Port in config.json ändern

4. **Service startet nicht**
   - Logs prüfen: `sudo journalctl -u marstek -n 50`
   - Berechtigungen prüfen
   - Python-Pfad in service-Datei prüfen

### Debug-Modus

Für detaillierte Ausgaben:

```bash
# Logging-Level in config.json auf "DEBUG" setzen
"logging": {
  "level": "DEBUG"
}
```

## 📊 Funktionsweise

### Regelungslogik

1. **Messung**: Energiemessgerät (Shelly/EcoTracker) misst aktuelle Netzleistung
2. **Durchschnitt**: Bildung eines gewichteten Durchschnitts der letzten 3 Messungen
3. **Berechnung**: Bestimmung der benötigten Akku-Leistung
4. **Verteilung**: Gleichmäßige Verteilung auf verfügbare Akkus
5. **Anpassung**: Kontinuierliche Nachregelung alle 2 Sekunden

### Sicherheitsfunktionen

- **Messgerät-Ausfall**: Akkus werden bei Kommunikationsausfall gestoppt
- **SoC-Grenzen**: Automatischer Schutz vor Tiefentladung/Überladung
- **Fehlertoleranz**: Teilweise funktionierende Systeme bleiben aktiv
- **Graceful Shutdown**: Sauberes Herunterfahren bei Systemstopp

## 🔄 EcoTracker vs. Shelly

### EcoTracker everHome
- **Vorteile**: Einfache REST-API, kompakte Daten
- **API-Endpunkt**: `http://<ip>/v1/json`
- **Datenformat**: JSON mit power, powerAvg, energyCounterIn/Out
- **Leistungskonvention**: Positiv = Bezug, Negativ = Einspeisung

### Shelly 3EM Pro
- **Vorteile**: Detaillierte Phasenmessung, umfangreiche Geräteinformationen
- **API-Endpunkt**: `http://<ip>/rpc/Shelly.GetStatus`
- **Datenformat**: JSON mit Einzelphasenwerten
- **Leistungskonvention**: Summierung aller drei Phasen

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE Datei für Details.

## 🤝 Support

Bei Fragen oder Problemen:
1. Prüfen Sie diese Dokumentation
2. Schauen Sie in die Log-Dateien
3. Erstellen Sie ein Issue im Repository

---

**Hinweis**: Dieses System arbeitet mit Hochspannung und sollte nur von qualifiziertem Personal installiert werden. Beachten Sie alle geltenden Sicherheitsvorschriften und Normen.
