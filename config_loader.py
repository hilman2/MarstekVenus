#!/usr/bin/env python3
"""
Einfacher Konfigurationsloader für Marstek PV-Akku Steuerung
Lädt nur aus config.json - keine Fallback-Werte!
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Lädt und validiert Konfiguration aus config.json"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """Lädt Konfiguration aus Datei - wirft Exception bei Fehlern"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {self.config_file}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self._validate_config()
            logger.info(f"Konfiguration geladen: {self.config_file}")
            return self.config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültige JSON-Syntax in {self.config_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _validate_config(self):
        """Validiert kritische Konfigurationswerte"""
        required_sections = ['battery', 'control', 'web']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Fehlende Konfigurationssektion: {section}")
        
        # Energy Meter Konfiguration
        if 'energy_meter' not in self.config:
            raise ValueError("Energy Meter Konfiguration fehlt")
        
        meter_type = self.config['energy_meter'].get('type', 'shelly')
        if meter_type not in ['shelly', 'ecotracker']:
            raise ValueError(f"Unbekannter Energy Meter Typ: {meter_type}")
        
        # Prüfe ob die Konfiguration für den gewählten Meter-Typ vorhanden ist
        if meter_type not in self.config:
            raise ValueError(f"Konfiguration für {meter_type} fehlt")
        
        meter_config = self.config[meter_type]
        if not meter_config.get('ip'):
            raise ValueError(f"{meter_type} IP-Adresse nicht konfiguriert")
        
        # Battery-Konfiguration
        battery = self.config['battery']
        if not battery.get('ip'):
            raise ValueError("Battery IP-Adresse nicht konfiguriert")
        if not battery.get('akku_ids') or not isinstance(battery['akku_ids'], list):
            raise ValueError("Akku-IDs nicht konfiguriert oder ungültig")
        
        # Validiere Akku-IDs
        akku_ids = battery['akku_ids']
        if not all(isinstance(id, int) and 1 <= id <= 20 for id in akku_ids):
            raise ValueError("Akku-IDs müssen Ganzzahlen zwischen 1 und 20 sein")
        
        # Port-Validierung
        if not (1 <= battery.get('port', 0) <= 65535):
            raise ValueError("Battery Port muss zwischen 1 und 65535 liegen")
        
        logger.info(f"Konfiguration validiert - Akkus: {akku_ids}")
    
    def get(self, path: str, default=None):
        """Holt Konfigurationswert über Punkt-Notation (z.B. 'shelly.ip')"""
        try:
            value = self.config
            for part in path.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            if default is None:
                raise KeyError(f"Konfigurationswert nicht gefunden: {path}")
            return default
    
    def get_energy_meter_type(self) -> str:
        """Gibt den konfigurierten Energy Meter Typ zurück"""
        return self.config.get('energy_meter', {}).get('type', 'shelly')
    
    def get_energy_meter_config(self) -> Dict[str, Any]:
        """Gibt die Konfiguration für den konfigurierten Energy Meter zurück"""
        meter_type = self.get_energy_meter_type()
        return self.config[meter_type]
    
    def get_shelly_config(self) -> Dict[str, Any]:
        """Gibt Shelly-Konfiguration zurück (für Abwärtskompatibilität)"""
        if self.get_energy_meter_type() == 'shelly':
            return self.config['shelly']
        else:
            # Falls EcoTracker konfiguriert ist, gib dessen Config zurück
            return self.get_energy_meter_config()
    
    def get_ecotracker_config(self) -> Dict[str, Any]:
        """Gibt EcoTracker-Konfiguration zurück"""
        return self.config.get('ecotracker', {})
    
    def get_battery_config(self) -> Dict[str, Any]:
        """Gibt Battery-Konfiguration zurück"""
        return self.config['battery']
    
    def get_control_config(self) -> Dict[str, Any]:
        """Gibt Control-Konfiguration zurück"""
        return self.config['control']
    
    def get_web_config(self) -> Dict[str, Any]:
        """Gibt Web-Konfiguration zurück"""
        return self.config['web']
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Gibt Logging-Konfiguration zurück"""
        return self.config.get('logging', {})

# Globale Instanz
config = ConfigLoader()

def load_config() -> Dict[str, Any]:
    """Lädt Konfiguration und gibt sie zurück"""
    return config.load()

def get_config() -> ConfigLoader:
    """Gibt Konfigurationsloader zurück"""
    return config