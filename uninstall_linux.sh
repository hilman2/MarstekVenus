#!/bin/bash
# Marstek PV-Akku Steuerung - Deinstallationsskript
# Für Debian/Ubuntu basierte Systeme

set -e

echo "============================================"
echo "Marstek PV-Akku Steuerung - Deinstallation"
echo "============================================"
echo

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
   exit 1
fi

# Sicherheitsabfrage
echo -e "${RED}WARNUNG: Dies wird die Marstek PV-Akku Steuerung vollständig entfernen!${NC}"
echo "Folgende Aktionen werden durchgeführt:"
echo "- Systemd Service stoppen und entfernen"
echo "- Installationsverzeichnis /opt/marstek löschen"
echo "- Log-Dateien entfernen"
echo
read -p "Sind Sie sicher, dass Sie fortfahren möchten? (ja/nein): " -r
if [[ ! $REPLY == "ja" ]]; then
    echo "Deinstallation abgebrochen."
    exit 0
fi

echo

# Service stoppen
if systemctl is-active --quiet marstek; then
    echo "Stoppe marstek Service..."
    sudo systemctl stop marstek
    print_success "Service gestoppt"
else
    print_warning "Service war nicht aktiv"
fi

# Service deaktivieren
if systemctl is-enabled --quiet marstek 2>/dev/null; then
    echo "Deaktiviere marstek Service..."
    sudo systemctl disable marstek
    print_success "Service deaktiviert"
fi

# Service-Datei entfernen
if [ -f "/etc/systemd/system/marstek.service" ]; then
    echo "Entferne Service-Datei..."
    sudo rm /etc/systemd/system/marstek.service
    sudo systemctl daemon-reload
    print_success "Service-Datei entfernt"
fi

# Log-Dateien entfernen
echo "Entferne Log-Dateien..."
sudo rm -f /var/log/marstek.log /var/log/marstek.error.log
print_success "Log-Dateien entfernt"

# Installationsverzeichnis entfernen
INSTALL_DIR="/opt/marstek"
if [ -d "$INSTALL_DIR" ]; then
    # Backup-Frage für config.json
    if [ -f "$INSTALL_DIR/config.json" ]; then
        echo
        read -p "Möchten Sie die config.json sichern? (j/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Jj]$ ]]; then
            cp "$INSTALL_DIR/config.json" "$HOME/marstek_config_backup_$(date +%Y%m%d_%H%M%S).json"
            print_success "Konfiguration gesichert in: $HOME/"
        fi
    fi
    
    echo "Entferne Installationsverzeichnis..."
    sudo rm -rf "$INSTALL_DIR"
    print_success "Installationsverzeichnis entfernt"
else
    print_warning "Installationsverzeichnis nicht gefunden"
fi

echo
echo "============================================"
echo -e "${GREEN}Deinstallation abgeschlossen!${NC}"
echo "============================================"
echo

# Prüfe ob noch Reste vorhanden sind
if command -v marstek &> /dev/null; then
    print_warning "Hinweis: marstek Befehl noch in PATH gefunden"
fi

print_success "Die Marstek PV-Akku Steuerung wurde vollständig entfernt."
