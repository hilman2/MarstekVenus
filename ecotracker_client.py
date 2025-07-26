#!/usr/bin/env python3
"""
EcoTracker Client für Marstek PV-Akku Steuerung
Mit Durchschnittsbildung der letzten 3 Abrufe für stabilere Regelung
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from collections import deque

logger = logging.getLogger(__name__)

class EcoTrackerClient:
    """EcoTracker Client mit 3-Werte-Durchschnittsbildung für stabilere Regelung"""
    
    def __init__(self, ip: str, timeout: int = 5):
        self.ip = ip
        self.timeout = timeout
        self.base_url = f"http://{ip}"
        self.failure_count = 0
        self.last_success = time.time()
        
        # Durchschnittsbildung der letzten 3 Abrufe
        self.power_history = deque(maxlen=3)
        self.last_poll_time = 0
        
        logger.info(f"EcoTracker-Client initialisiert: {ip} (mit 3-Werte-Durchschnitt)")
    
    def poll_current_power(self) -> Optional[float]:
        """
        Holt AKTUELLE Leistung vom EcoTracker und fügt sie zur History hinzu
        Returns: Aktuelle Leistung in Watt (positiv=Bezug, negativ=Einspeisung) oder None bei Fehler
        """
        try:
            url = f"{self.base_url}/v1/json"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Leistung aus EcoTracker-Daten (bereits in Watt)
            # Positiv = Bezug, Negativ = Einspeisung (laut API-Doku)
            current_power = float(data.get('power', 0))
            current_time = time.time()
            
            # Zur History hinzufügen
            self.power_history.append({
                'power': current_power,
                'timestamp': current_time
            })
            self.last_poll_time = current_time
            
            # Erfolg - Fehlerzähler zurücksetzen
            if self.failure_count > 0:
                logger.debug(f"EcoTracker-Verbindung wiederhergestellt nach {self.failure_count} Fehlern")
                self.failure_count = 0
            
            self.last_success = current_time
            return current_power
            
        except requests.exceptions.Timeout:
            self.failure_count += 1
            logger.warning(f"EcoTracker-Timeout ({self.failure_count}) - {self.ip}")
            return None
            
        except requests.exceptions.ConnectionError:
            self.failure_count += 1
            logger.warning(f"EcoTracker-Verbindungsfehler ({self.failure_count}) - {self.ip}")
            return None
            
        except Exception as e:
            self.failure_count += 1
            logger.error(f"EcoTracker-Fehler ({self.failure_count}) - {self.ip}: {e}")
            return None
    
    def get_power(self) -> Optional[float]:
        """
        Gibt Durchschnittswert der letzten 3 EcoTracker-Abrufe zurück
        Returns: Durchschnittliche Leistung in Watt oder None bei Fehler
        """
        if not self.power_history:
            # Keine Daten vorhanden - ersten Abruf machen
            current = self.poll_current_power()
            return current if current is not None else None
        
        # Durchschnitt der verfügbaren Werte berechnen
        if len(self.power_history) == 1:
            return self.power_history[0]['power']
        
        # Gewichteter Durchschnitt: neueste Werte haben mehr Gewicht
        total_weight = 0
        weighted_sum = 0
        
        for i, entry in enumerate(self.power_history):
            weight = i + 1  # Neueste Werte bekommen höheres Gewicht
            weighted_sum += entry['power'] * weight
            total_weight += weight
        
        average_power = weighted_sum / total_weight
        
        logger.debug(f"EcoTracker-Durchschnitt: {average_power:.1f}W aus {len(self.power_history)} Werten")
        return average_power
    
    def get_current_power_direct(self) -> Optional[float]:
        """
        Direkter Abruf ohne History für Web-Interface oder Diagnose
        Returns: Aktuelle Leistung in Watt oder None bei Fehler  
        """
        return self.poll_current_power()
    
    def get_detailed_power(self) -> Optional[Dict[str, float]]:
        """
        Holt detaillierte Leistungsdaten vom EcoTracker
        Returns: Dict mit power, powerAvg, energyCounterIn, energyCounterOut oder None
        """
        try:
            url = f"{self.base_url}/v1/json"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'power': float(data.get('power', 0)),
                'powerAvg': float(data.get('powerAvg', 0)),
                'energyCounterIn': float(data.get('energyCounterIn', 0)),
                'energyCounterInT1': float(data.get('energyCounterInT1', 0)) if 'energyCounterInT1' in data else None,
                'energyCounterInT2': float(data.get('energyCounterInT2', 0)) if 'energyCounterInT2' in data else None,
                'energyCounterOut': float(data.get('energyCounterOut', 0))
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der detaillierten EcoTracker-Daten: {e}")
            return None
    
    def is_online(self) -> bool:
        """Prüft ob EcoTracker erreichbar ist"""
        try:
            url = f"{self.base_url}/v1/json"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Holt Geräteinformationen vom EcoTracker
        Da EcoTracker keine separaten Geräteinformationen liefert, geben wir die verfügbaren Daten zurück
        """
        try:
            detailed = self.get_detailed_power()
            if detailed:
                return {
                    'type': 'EcoTracker',
                    'ip': self.ip,
                    'api_version': 'v1',
                    'data': detailed
                }
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der EcoTracker-Geräteinformationen: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Status des EcoTracker-Clients zurück"""
        current_time = time.time()
        history_info = {
            'count': len(self.power_history),
            'values': [entry['power'] for entry in self.power_history] if self.power_history else [],
            'timestamps': [entry['timestamp'] for entry in self.power_history] if self.power_history else [],
            'last_poll': self.last_poll_time,
            'seconds_since_poll': int(current_time - self.last_poll_time) if self.last_poll_time > 0 else 0
        }
        
        return {
            'ip': self.ip,
            'online': self.is_online(),
            'failure_count': self.failure_count,
            'last_success': self.last_success,
            'seconds_since_success': int(current_time - self.last_success),
            'history': history_info,
            'current_average': self.get_power()
        }
    
    def reset_failure_count(self):
        """Setzt Fehlerzähler zurück"""
        self.failure_count = 0
        logger.info(f"EcoTracker-Fehlerzähler zurückgesetzt: {self.ip}")
