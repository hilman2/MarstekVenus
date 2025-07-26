#!/bin/bash
# Marstek PV-Akku Steuerung - Linux Installationsskript
# Für Debian/Ubuntu basierte Systeme

set -e  # Bei Fehler abbrechen

echo "============================================"
echo "Marstek PV-Akku Steuerung - Installation"
echo "============================================"
echo

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion für farbige Ausgabe
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Root-Rechte prüfen
if [[ $EUID -eq 0 ]]; then
   print_warning "Dieses Skript sollte NICHT als root ausgeführt werden!"
   print_warning "Es wird sudo verwenden, wenn nötig."
   exit 1
fi

# System aktualisieren
echo "Aktualisiere Paketlisten..."
sudo apt update

# Benötigte Pakete installieren
echo "Installiere benötigte Pakete..."
sudo apt install -y python3 python3-pip python3-venv git

# Python-Version prüfen
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    print_error "Python $python_version gefunden, aber $required_version oder höher benötigt!"
    exit 1
else
    print_success "Python $python_version gefunden"
fi

# Installationsverzeichnis
INSTALL_DIR="/opt/marstek"
echo
echo "Installationsverzeichnis: $INSTALL_DIR"

# Verzeichnis erstellen
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Erstelle Installationsverzeichnis..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    print_success "Verzeichnis erstellt"
else
    print_warning "Verzeichnis existiert bereits"
fi

# Ins Verzeichnis wechseln
cd "$INSTALL_DIR"

# Aktuelle Dateien kopieren
echo
echo "Kopiere Projektdateien..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Nur Python-Dateien und Konfiguration kopieren
for file in main.py battery_client.py shelly_client.py zero_feed_control.py web_server.py config_loader.py requirements.txt config.example.json; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp "$SCRIPT_DIR/$file" "$INSTALL_DIR/"
        print_success "Kopiert: $file"
    else
        print_warning "Nicht gefunden: $file"
    fi
done

# Virtuelle Umgebung erstellen
echo
echo "Erstelle Python virtuelle Umgebung..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtuelle Umgebung erstellt"
else
    print_warning "Virtuelle Umgebung existiert bereits"
fi

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# pip aktualisieren
echo
echo "Aktualisiere pip..."
pip install --upgrade pip

# Abhängigkeiten installieren
echo
echo "Installiere Python-Abhängigkeiten..."
pip install -r requirements.txt
print_success "Abhängigkeiten installiert"

# Konfiguration erstellen
echo
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        cp config.example.json config.json
        print_success "Beispielkonfiguration kopiert"
        print_warning "WICHTIG: Bitte passen Sie config.json an Ihre Umgebung an!"
        echo "         - Shelly IP-Adresse"
        echo "         - Marstek Gateway IP-Adresse"
        echo "         - Akku IDs"
    fi
else
    print_warning "config.json existiert bereits"
fi

# Log-Verzeichnis erstellen
if [ ! -d "logs" ]; then
    mkdir logs
    print_success "Log-Verzeichnis erstellt"
fi

# Systemd Service erstellen
echo
echo "Erstelle systemd Service..."
SERVICE_FILE="/etc/systemd/system/marstek.service"

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Marstek PV-Akku Steuerung
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/marstek.log
StandardError=append:/var/log/marstek.error.log

[Install]
WantedBy=multi-user.target
EOF

print_success "Service-Datei erstellt"

# Service aktivieren
echo
echo "Aktiviere systemd Service..."
sudo systemctl daemon-reload
sudo systemctl enable marstek.service
print_success "Service aktiviert (Autostart)"

# Berechtigungen für Log-Dateien
sudo touch /var/log/marstek.log /var/log/marstek.error.log
sudo chown $USER:$USER /var/log/marstek.log /var/log/marstek.error.log

echo
echo "============================================"
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo "============================================"
echo
echo "Nächste Schritte:"
echo "1. Konfiguration anpassen:"
echo "   nano $INSTALL_DIR/config.json"
echo
echo "2. Service starten:"
echo "   sudo systemctl start marstek"
echo
echo "3. Status prüfen:"
echo "   sudo systemctl status marstek"
echo
echo "4. Logs anzeigen:"
echo "   sudo journalctl -u marstek -f"
echo
echo "5. Web-Dashboard öffnen:"
echo "   http://localhost:8080"
echo

# Frage ob config.json bearbeitet werden soll
read -p "Möchten Sie die Konfiguration jetzt anpassen? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    nano "$INSTALL_DIR/config.json"
fi

# Frage ob Service gestartet werden soll
read -p "Möchten Sie den Service jetzt starten? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    sudo systemctl start marstek
    sleep 2
    sudo systemctl status marstek --no-pager
    echo
    print_success "Web-Dashboard: http://localhost:8080"
fi

echo
print_success "Installation erfolgreich abgeschlossen!"
