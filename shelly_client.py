#!/usr/bin/env python3
"""
Shelly 3EM Pro Client für Marstek PV-Akku Steuerung
Mit Durchschnittsbildung der letzten 3 Abrufe für stabilere Regelung
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from collections import deque

logger = logging.getLogger(__name__)

class ShellyClient:
    """Shelly Client mit 3-Werte-Durchschnittsbildung für stabilere Regelung"""
    
    def __init__(self, ip: str, timeout: int = 5):
        self.ip = ip
        self.timeout = timeout
        self.base_url = f"http://{ip}"
        self.failure_count = 0
        self.last_success = time.time()
        
        # Durchschnittsbildung der letzten 3 Abrufe
        self.power_history = deque(maxlen=3)
        self.last_poll_time = 0
        
        logger.info(f"Shelly-Client initialisiert: {ip} (mit 3-Werte-Durchschnitt)")
    
    def poll_current_power(self) -> Optional[float]:
        """
        Holt AKTUELLE Leistung vom Shelly und fügt sie zur History hinzu
        Returns: Aktuelle Leistung in Watt (positiv=Bezug, negativ=Einspeisung) oder None bei Fehler
        """
        try:
            url = f"{self.base_url}/rpc/Shelly.GetStatus"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            em_data = data.get('em:0', {})
            
            # Leistung aller drei Phasen summieren
            power_a = float(em_data.get('a_act_power', 0))
            power_b = float(em_data.get('b_act_power', 0)) 
            power_c = float(em_data.get('c_act_power', 0))
            
            current_power = power_a + power_b + power_c
            current_time = time.time()
            
            # Zur History hinzufügen
            self.power_history.append({
                'power': current_power,
                'timestamp': current_time
            })
            self.last_poll_time = current_time
            
            # Erfolg - Fehlerzähler zurücksetzen
            if self.failure_count > 0:
                logger.debug(f"Shelly-Verbindung wiederhergestellt nach {self.failure_count} Fehlern")
                self.failure_count = 0
            
            self.last_success = current_time
            return current_power
            
        except requests.exceptions.Timeout:
            self.failure_count += 1
            logger.warning(f"Shelly-Timeout ({self.failure_count}) - {self.ip}")
            return None
            
        except requests.exceptions.ConnectionError:
            self.failure_count += 1
            logger.warning(f"Shelly-Verbindungsfehler ({self.failure_count}) - {self.ip}")
            return None
            
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Shelly-Fehler ({self.failure_count}) - {self.ip}: {e}")
            return None
    
    def get_power(self) -> Optional[float]:
        """
        Gibt Durchschnittswert der letzten 3 Shelly-Abrufe zurück
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
        
        logger.debug(f"Shelly-Durchschnitt: {average_power:.1f}W aus {len(self.power_history)} Werten")
        return average_power
    
    def get_current_power_direct(self) -> Optional[float]:
        """
        Direkter Abruf ohne History für Web-Interface oder Diagnose
        Returns: Aktuelle Leistung in Watt oder None bei Fehler  
        """
        return self.poll_current_power()
    
    def get_detailed_power(self) -> Optional[Dict[str, float]]:
        """
        Holt detaillierte Leistungsdaten aller Phasen
        Returns: Dict mit phase_a, phase_b, phase_c, total oder None
        """
        try:
            url = f"{self.base_url}/rpc/Shelly.GetStatus"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            em_data = data.get('em:0', {})
            
            power_a = float(em_data.get('a_act_power', 0))
            power_b = float(em_data.get('b_act_power', 0))
            power_c = float(em_data.get('c_act_power', 0))
            
            return {
                'phase_a': power_a,
                'phase_b': power_b, 
                'phase_c': power_c,
                'total': power_a + power_b + power_c
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der detaillierten Shelly-Daten: {e}")
            return None
    
    def is_online(self) -> bool:
        """Prüft ob Shelly erreichbar ist"""
        try:
            url = f"{self.base_url}/rpc/Shelly.GetDeviceInfo"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Holt Geräteinformationen vom Shelly"""
        try:
            url = f"{self.base_url}/rpc/Shelly.GetDeviceInfo"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Shelly-Geräteinformationen: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Status des Shelly-Clients zurück"""
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
        logger.info(f"Shelly-Fehlerzähler zurückgesetzt: {self.ip}")