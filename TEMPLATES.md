# Template-System Dokumentation

## Struktur

```
MarstekVenus/
├── templates/                 # HTML Templates
│   └── dashboard.html        # Haupt-Dashboard
├── static/                   # Statische Dateien  
│   ├── css/                  # Stylesheets
│   │   ├── base.css         # Gemeinsame Basis-Styles
│   │   └── dashboard.css    # Dashboard-spezifische Styles
│   └── js/                  # JavaScript-Dateien
│       └── dashboard.js     # Dashboard-Funktionalität
├── web_server.py            # Flask-Server mit Template-Support
├── templates.py             # Legacy Setup-Template (wird noch verwendet)
└── web_config.py           # Config-Template (wird noch verwendet)
```

## Features

### Modulares CSS-System
- **base.css**: Gemeinsame CSS-Variablen, Utility-Classes und Basis-Komponenten
- **dashboard.css**: Dashboard-spezifische Styles
- CSS-Variablen für konsistente Farben und Abstände
- Dark Mode Design mit Home Assistant Inspiration

### Template-System
- Flask Templates im `templates/` Verzeichnis
- Statische Dateien im `static/` Verzeichnis
- Automatisches Serving von CSS/JS-Dateien

### JavaScript-Module
- Separate JS-Dateien für jede Seite
- Modulare Funktionen für API-Calls und UI-Updates

## Verwendung

### Neue Seite hinzufügen

1. **HTML-Template erstellen** (`templates/neue_seite.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neue Seite</title>
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/neue_seite.css">
</head>
<body>
    <!-- Inhalt -->
    <script src="/static/js/neue_seite.js"></script>
</body>
</html>
```

2. **CSS-Datei erstellen** (`static/css/neue_seite.css`):
```css
/* Seiten-spezifische Styles - Base CSS wird automatisch geladen */

.meine-klasse {
    color: var(--primary-color);
    padding: var(--spacing-md);
}
```

3. **JavaScript-Datei erstellen** (`static/js/neue_seite.js`):
```javascript
// Seiten-spezifische Funktionalität

function meineFunction() {
    // Code hier
}

window.addEventListener('load', () => {
    // Initialisierung
});
```

4. **Route in web_server.py hinzufügen**:
```python
@self.app.route('/neue_seite')
def neue_seite():
    return render_template('neue_seite.html')
```

## CSS-Variablen (base.css)

### Farben
- `--primary-color`: #03a9f4 (Blau)
- `--success-color`: #4caf50 (Grün)
- `--warning-color`: #ff9800 (Orange)
- `--error-color`: #f44336 (Rot)

### Abstände
- `--spacing-xs`: 0.25rem
- `--spacing-sm`: 0.5rem
- `--spacing-md`: 1rem
- `--spacing-lg`: 1.5rem
- `--spacing-xl`: 2rem

### Utility Classes
- `.text-primary`, `.text-secondary`, `.text-disabled`
- `.text-success`, `.text-warning`, `.text-error`
- `.status-indicator`, `.status-dot`
- `.button`, `.button-primary`, `.button-secondary`
- `.card`, `.card-title`
- `.grid`, `.grid-2`, `.grid-3`

## Migration von Legacy-Templates

Die Setup- und Config-Seiten verwenden noch das alte System in `templates.py` und `web_config.py`. Diese können schrittweise migriert werden:

1. HTML aus Python-Strings in separate `.html`-Dateien extrahieren
2. CSS in separate `.css`-Dateien mit `base.css` als Basis
3. JavaScript in separate `.js`-Dateien
4. Routes in `web_server.py` auf `render_template()` umstellen

## Vorteile

- **Bessere Wartbarkeit**: HTML, CSS und JS sind getrennt
- **Wiederverwendbare Komponenten**: Gemeinsame Styles in base.css
- **Entwicklerfreundlich**: Syntax-Highlighting und Autocomplete
- **Modulare Struktur**: Jede Seite hat ihre eigenen Assets
- **Einfache Erweiterung**: Neue Seiten folgen einem klaren Muster
