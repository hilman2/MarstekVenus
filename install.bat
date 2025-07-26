@echo off
REM Marstek PV-Akku Steuerung - Windows Installation
REM Führen Sie diese Datei als Administrator aus

echo ============================================
echo Marstek PV-Akku Steuerung - Installation
echo ============================================
echo.

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert!
    echo Bitte installieren Sie Python 3.8 oder höher von https://www.python.org
    echo Stellen Sie sicher, dass Python zum PATH hinzugefügt wurde.
    pause
    exit /b 1
)

echo Python gefunden:
python --version
echo.

REM Erstelle virtuelle Umgebung
echo Erstelle virtuelle Umgebung...
if exist venv (
    echo Virtuelle Umgebung existiert bereits, überspringe...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo FEHLER: Konnte virtuelle Umgebung nicht erstellen!
        pause
        exit /b 1
    )
)
echo.

REM Aktiviere virtuelle Umgebung
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo FEHLER: Konnte virtuelle Umgebung nicht aktivieren!
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo Aktualisiere pip...
python -m pip install --upgrade pip
echo.

REM Installiere Abhängigkeiten
echo Installiere Abhängigkeiten...
pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Konnte Abhängigkeiten nicht installieren!
    pause
    exit /b 1
)
echo.

REM Erstelle Beispielkonfiguration wenn nicht vorhanden
if not exist config.json (
    echo Erstelle Beispielkonfiguration...
    if exist config.example.json (
        copy config.example.json config.json
        echo.
        echo WICHTIG: Bitte passen Sie die config.json an Ihre Umgebung an!
        echo          - Shelly IP-Adresse
        echo          - Marstek Gateway IP-Adresse
        echo          - Akku IDs
        echo.
        notepad config.json
    ) else (
        echo WARNUNG: config.example.json nicht gefunden!
        echo          Bitte erstellen Sie eine config.json manuell.
    )
)
echo.

REM Erstelle Log-Verzeichnis
if not exist logs (
    echo Erstelle Log-Verzeichnis...
    mkdir logs
)
echo.

REM Erstelle Start-Skript
echo Erstelle Start-Skript...
(
echo @echo off
echo echo Starte Marstek PV-Akku Steuerung...
echo call venv\Scripts\activate.bat
echo python main.py
echo pause
) > start_marstek.bat
echo.

echo ============================================
echo Installation abgeschlossen!
echo ============================================
echo.
echo Nächste Schritte:
echo 1. Passen Sie die config.json an Ihre Umgebung an
echo 2. Starten Sie das System mit: start_marstek.bat
echo 3. Öffnen Sie das Web-Dashboard: http://localhost:8080
echo.
echo Für automatischen Start bei Windows-Start:
echo - Erstellen Sie eine Verknüpfung zu start_marstek.bat
echo - Kopieren Sie diese in den Autostart-Ordner
echo   (Win+R, shell:startup)
echo.

REM Frage ob System jetzt gestartet werden soll
set /p start_now="Möchten Sie das System jetzt starten? (j/n): "
if /i "%start_now%"=="j" (
    echo.
    echo Starte Marstek PV-Akku Steuerung...
    python main.py
) else (
    echo.
    echo Sie können das System später mit start_marstek.bat starten.
)

pause
