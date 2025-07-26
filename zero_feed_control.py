#!/usr/bin/env python3
"""
Zero-Feed-Controller für Marstek PV-Akku Steuerung
Intelligente Regelung: Ziel ±0 Watt am Shelly (Netzanschlusspunkt)

KORRIGIERTE STEUERUNG V3.4:
- Stabilere Regelung durch Priorisierung der Leistungsanpassung über Modus-Wechsel
- KORRIGIERTE PHYSIK für robuste Berechnung
- ÄNDERUNGSRATE-BEGRENZUNG für träge, sanfte Regelung (max 750W/Zyklus)
- NIEDRIG-SoC SCHUTZ: Laden erst ab 100W Überschuss wenn SoC < 13%
- WEB-INTEGRATION: Regelungslogs erscheinen auf Webseite
- Verhindert Oszillation bei Laständerungen
- Bei Entladung: Ziel +20W Grid
- Bei Ladung: Ziel -20W Grid
"""

import logging
import time
from typing import Optional, Tuple, Dict, Any
from shelly_client import ShellyClient
from battery_client import BatteryManager
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class ZeroFeedController:
    """Intelligenter Zero-Feed-Controller mit träger Regelung und Web-Integration"""
    
    def __init__(self, shelly_client, battery_manager: BatteryManager, config: ConfigLoader, web_server=None):
        self.energy_meter = shelly_client  # Kann ShellyClient oder EcoTrackerClient sein
        self.batteries = battery_manager
        self.config = config
        self.web_server = web_server  # Web-Server Referenz für Logging
        
        # Konfiguration laden
        control_config = config.get_control_config()
        battery_config = config.get_battery_config()
        
        # Regelungs-Parameter
        self.target_grid_power_charge = control_config.get('target_grid_power_charge', -20)
        self.target_grid_power_discharge = control_config.get('target_grid_power_discharge', 20)
        
        # Akku-Parameter
        self.max_power_per_battery = battery_config['max_power_per_battery']
        self.min_power_per_battery = battery_config['min_power_per_battery']
        self.min_soc_discharge = battery_config['min_soc_for_discharge']
        self.max_soc_charge = battery_config['max_soc_for_charge']
        
        # Status-Tracking
        self.current_mode = 0  # 0=stop, 1=charge, 2=discharge
        self.current_total_power = 0.0
        self.last_grid_power = 0.0
        self.mode_change_count = 0
        
        # Trägheit für sanfte Regelung
        self.max_power_change_rate = 750  # Maximale Änderung pro Zyklus in Watt
        
        # Schutzregelung für niedrigen SoC
        self.low_soc_threshold = 13  # Unter 13% SoC
        self.low_soc_min_surplus = -100  # Mindestens 100W Überschuss nötig
        
        logger.info("Zero-Feed-Controller initialisiert (v3.4 - Web-Integration)")
        logger.info(f"Grid-Ziele: Laden bis {self.target_grid_power_charge}W, Entladen bis {self.target_grid_power_discharge}W")
        logger.info(f"Akku-Grenzen: {self.min_power_per_battery}-{self.max_power_per_battery}W, SoC {self.min_soc_discharge}-{self.max_soc_charge}%")
        logger.info(f"Änderungsrate begrenzt auf: {self.max_power_change_rate}W/Zyklus")
        logger.info(f"Niedrig-SoC Schutz: <{self.low_soc_threshold}% benötigt >{abs(self.low_soc_min_surplus)}W Überschuss")

    def execute_control_cycle(self) -> Tuple[bool, str]:
        """Führt einen kompletten Regelzyklus aus"""
        try:
            grid_power = self.energy_meter.get_current_power_direct()
            if grid_power is None:
                meter_type = self.config.get_energy_meter_type()
                return False, f"{meter_type}-Daten nicht verfügbar"
            
            avg_soc = self.batteries.get_average_soc()
            
            success, new_mode, new_power, reasoning = self._calculate_optimal_control(
                grid_power, avg_soc, self.current_mode, self.current_total_power
            )
            
            if not success:
                self.batteries.stop_all()
                self.current_mode = 0
                self.current_total_power = 0
                return False, reasoning
            
            # Trägheit anwenden
            new_mode, new_power, rate_limited = self._apply_rate_limiting(new_mode, new_power)
            
            # Nur bei Änderungen handeln
            mode_changed = (new_mode != self.current_mode)
            power_changed_significantly = abs(new_power - self.current_total_power) > self.min_power_per_battery / 2

            if mode_changed or power_changed_significantly:
                # **STRUKTURIERTER LOG für Konsole UND Web-Interface**
                old_mode_text = {0: 'Stop', 1: 'Laden', 2: 'Entladen'}.get(self.current_mode, 'Unbekannt')
                new_mode_text = {0: 'Stop', 1: 'Laden', 2: 'Entladen'}.get(new_mode, 'Unbekannt')
                
                # Log-Nachricht erstellen
                meter_type = self.config.get_energy_meter_type()
                if mode_changed:
                    log_msg = f"{meter_type}: {grid_power:.0f}W | Modus {old_mode_text} -> {new_mode_text} | Leistung {self.current_total_power:.0f}W -> {new_power:.0f}W"
                else:
                    log_msg = f"{meter_type}: {grid_power:.0f}W | Modus {new_mode_text} | Leistung {self.current_total_power:.0f}W -> {new_power:.0f}W"
                
                # Rate-Limited Kennzeichnung
                if rate_limited:
                    log_msg += " [GEDÄMPFT]"
                
                # **DOPPELTES LOGGING: Konsole + Web-Interface**
                logger.info(log_msg)
                if self.web_server:
                    log_level = 'warning' if rate_limited else 'info'
                    self.web_server.add_log_entry(log_level, log_msg)
                
                # Akku-Steuerung ausführen
                success = self._execute_battery_control(new_mode, new_power)
                if success:
                    if mode_changed:
                        self.mode_change_count += 1
                    
                    self.current_mode = new_mode
                    self.current_total_power = new_power
                else:
                    error_msg = "Akku-Steuerung fehlgeschlagen"
                    logger.error(error_msg)
                    if self.web_server:
                        self.web_server.add_log_entry('error', error_msg)
                    return False, error_msg
            
            self.last_grid_power = grid_power
            mode_text = {0: 'Stop', 1: 'Laden', 2: 'Entladen'}.get(new_mode, 'Unbekannt')
            
            status_suffix = " [GEDÄMPFT]" if rate_limited else ""
            status = f"{mode_text} {new_power:.0f}W | SoC: {avg_soc:.0f}% | {reasoning}{status_suffix}"
            return True, status
            
        except Exception as e:
            error_msg = f"Regelzyklus-Fehler: {e}"
            logger.error(error_msg, exc_info=True)
            if self.web_server:
                self.web_server.add_log_entry('error', error_msg)
            return False, error_msg

    def _apply_rate_limiting(self, target_mode: int, target_power: float) -> Tuple[int, float, bool]:
        """
        Begrenzt die Änderungsrate der Leistung für sanfte Regelung
        
        Returns: (final_mode, final_power, was_rate_limited)
        """
        
        # Bei Stop-Befehlen: Immer sofort (Sicherheit)
        if target_mode == 0:
            return 0, 0.0, False
        
        # Start aus Stop-Modus: Sanft hochfahren
        if self.current_mode == 0 and target_mode != 0:
            if target_power > self.max_power_change_rate:
                limited_power = min(target_power, self.max_power_change_rate)
                return target_mode, limited_power, True
            else:
                return target_mode, target_power, False
        
        # Modus-Wechsel zwischen Laden/Entladen: Auch gedämpft
        elif self.current_mode != target_mode:
            if target_power > self.max_power_change_rate:
                limited_power = min(target_power, self.max_power_change_rate)
                return target_mode, limited_power, True
            else:
                return target_mode, target_power, False
        
        else:
            # Gleicher Modus: Leistungsänderung begrenzen
            power_change = target_power - self.current_total_power
            
            if abs(power_change) <= self.max_power_change_rate:
                return target_mode, target_power, False
            else:
                # Änderung begrenzen
                if power_change > 0:
                    limited_power = self.current_total_power + self.max_power_change_rate
                else:
                    limited_power = self.current_total_power - self.max_power_change_rate
                
                limited_power = max(0, limited_power)
                return target_mode, limited_power, True

    def _calculate_optimal_control(self, grid_power: float, avg_soc: float, current_mode: int, current_power: float) -> Tuple[bool, int, float, str]:
        """
        Berechnet optimale Akkuregelung mit korrekter Physik
        
        WICHTIG: current_power ist immer POSITIV (Betrag der Akku-Leistung)
        """
        
        if avg_soc is None:
            return False, 0, 0, "Kein SoC verfügbar"

        # Grenzen definieren
        min_power = self.min_power_per_battery
        max_charge_power = self._get_max_total_charge_power()
        max_discharge_power = self._get_max_total_discharge_power()

        # === MODUS: ENTLADEN (Mode 2) ===
        if current_mode == 2:
            
            # SoC-Check
            if avg_soc <= self.min_soc_discharge:
                return True, 0, 0, f"SoC {avg_soc:.0f}% zu niedrig - Entladung gestoppt"
            
            # PHYSIK: Gesamtverbrauch = Grid + Entladung
            total_consumption = grid_power + current_power
            
            # **FLEXIBLE ZIELWERTE je nach verfügbarer Entladeleistung**
            if total_consumption >= (min_power + self.target_grid_power_discharge):
                # Genug Verbrauch für Mindestleistung + Zielabstand (+20W)
                target_discharge = total_consumption - self.target_grid_power_discharge
                goal_text = f"Ziel {self.target_grid_power_discharge}W"
            else:
                # Wenig Verbrauch: Ziel 0W statt +20W (flexibles Ziel!)
                target_discharge = total_consumption  # Allen Verbrauch abdecken
                goal_text = "Ziel 0W (flexibel)"
            
            # Grenzen prüfen
            if target_discharge < min_power:
                return True, 0, 0, f"Entladung gestoppt - Verbrauch zu gering für Mindestleistung ({total_consumption:.0f}W < {min_power}W)"
            
            elif target_discharge > max_discharge_power:
                return True, 2, max_discharge_power, f"Maximal-Entladung {max_discharge_power:.0f}W (Verbrauch={total_consumption:.0f}W, {goal_text})"
            
            else:
                return True, 2, target_discharge, f"Entladung angepasst: {target_discharge:.0f}W (Verbrauch={total_consumption:.0f}W, {goal_text})"

        # === MODUS: LADEN (Mode 1) ===
        elif current_mode == 1:
            
            # SoC-Check
            if avg_soc >= self.max_soc_charge:
                return True, 0, 0, f"SoC {avg_soc:.0f}% zu hoch - Ladung gestoppt"
            
            # **WICHTIG: Niedrig-SoC Schutz NUR beim Start, NICHT beim laufenden Betrieb!**
            # Wenn bereits am Laden, normale Physik-Regelung verwenden
            
            # KORRIGIERTE PHYSIK für Laden:
            if grid_power >= 0:
                # NETZBEZUG während Laden → PV reicht nicht vollständig!
                actual_pv_production = current_power - grid_power
                
                if actual_pv_production <= 0:
                    return True, 0, 0, f"Ladung gestoppt - keine PV (Netzbezug {grid_power:.0f}W)"
                
                # **FLEXIBLE ZIELWERTE je nach verfügbarer PV-Leistung**
                if actual_pv_production >= (min_power + abs(self.target_grid_power_charge)):
                    # Genug PV für Mindestleistung + Zielabstand (-20W)
                    target_charge = actual_pv_production - abs(self.target_grid_power_charge)
                    goal_text = f"Ziel {self.target_grid_power_charge}W"
                else:
                    # Wenig PV: Ziel 0W statt -20W (flexibles Ziel!)
                    target_charge = actual_pv_production  # Alle verfügbare PV nutzen
                    goal_text = "Ziel 0W (flexibel)"
                
                if target_charge < min_power:
                    return True, 0, 0, f"Ladung gestoppt - PV zu schwach für Mindestleistung ({actual_pv_production:.0f}W < {min_power}W)"
                
                optimal_charge = min(target_charge, max_charge_power)
                return True, 1, optimal_charge, f"Ladung angepasst: {optimal_charge:.0f}W (PV={actual_pv_production:.0f}W, {goal_text})"
            
            else:
                # NETZEXPORT während Laden → PV ist stark genug
                actual_pv_production = current_power + abs(grid_power)
                
                # Bei Export immer das normale Ziel -20W anstreben
                target_charge = actual_pv_production - abs(self.target_grid_power_charge)
                
                if target_charge < min_power:
                    return True, 0, 0, f"Ladung gestoppt - PV zu schwach (brauche nur {target_charge:.0f}W)"
                
                elif target_charge > max_charge_power:
                    return True, 1, max_charge_power, f"Maximal-Ladung {max_charge_power:.0f}W (PV={actual_pv_production:.0f}W)"
                
                else:
                    return True, 1, target_charge, f"Ladung angepasst: {target_charge:.0f}W"

        # === MODUS: STOP (Mode 0) ===
        else:
            
            # Schwellenwerte für Start aus Stop-Modus
            START_THRESHOLD = 50  # Mindestens 50W Abweichung für Start
            
            # PV-Überschuss?
            if grid_power < (self.target_grid_power_charge - START_THRESHOLD):
                
                if avg_soc >= self.max_soc_charge:
                    return True, 0, 0, f"SoC {avg_soc:.0f}% zu hoch zum Laden"
                
                # **NIEDRIG-SOC SCHUTZ: Bei niedrigem SoC strengere Start-Anforderungen**
                if avg_soc < self.low_soc_threshold:
                    if grid_power > self.low_soc_min_surplus:
                        # Nicht genug Überschuss für niedrigen SoC
                        return True, 0, 0, f"SoC {avg_soc:.0f}% niedrig - brauche >{abs(self.low_soc_min_surplus)}W Überschuss für Start (nur {abs(grid_power):.0f}W)"
                
                available_pv = abs(grid_power)
                required_charge = available_pv - abs(self.target_grid_power_charge)
                
                if required_charge >= min_power:
                    optimal_charge = min(required_charge, max_charge_power)
                    return True, 1, optimal_charge, f"Start Laden: {optimal_charge:.0f}W (PV={available_pv:.0f}W)"
                else:
                    return True, 0, 0, f"PV zu schwach zum Laden ({available_pv:.0f}W)"
            
            # Netzbezug?
            elif grid_power > (self.target_grid_power_discharge + START_THRESHOLD):
                
                if avg_soc <= self.min_soc_discharge:
                    return True, 0, 0, f"SoC {avg_soc:.0f}% zu niedrig zum Entladen"
                
                required_discharge = grid_power - self.target_grid_power_discharge
                
                if required_discharge >= min_power:
                    optimal_discharge = min(required_discharge, max_discharge_power)
                    return True, 2, optimal_discharge, f"Start Entladen: {optimal_discharge:.0f}W (Verbrauch={grid_power:.0f}W)"
                else:
                    return True, 0, 0, f"Netzbezug zu gering zum Entladen ({grid_power:.0f}W)"
            
            # Im Zielbereich
            else:
                return True, 0, 0, f"Grid optimal: {grid_power:.0f}W (Ziel: {self.target_grid_power_charge}W bis {self.target_grid_power_discharge}W)"

    def _get_max_total_charge_power(self) -> float:
        available_count = self._count_available_batteries_for_charging()
        return available_count * self.max_power_per_battery
    
    def _get_max_total_discharge_power(self) -> float:
        available_count = self._count_available_batteries_for_discharging()
        return available_count * self.max_power_per_battery
    
    def _get_min_total_power(self) -> float:
        return self.min_power_per_battery

    def _count_available_batteries_for_charging(self) -> int:
        count = 0
        for battery in self.batteries.batteries.values():
            if battery.last_soc is not None and battery.last_soc < self.max_soc_charge:
                count += 1
        return count
    
    def _count_available_batteries_for_discharging(self) -> int:
        count = 0
        for battery in self.batteries.batteries.values():
            if battery.last_soc is not None and battery.last_soc > self.min_soc_discharge:
                count += 1
        return count
    
    def _execute_battery_control(self, mode: int, total_power: float) -> bool:
        try:
            if mode == 0:
                success = self.batteries.stop_all()
                # Reduziertes Logging - nur bei Fehlern interessant
                if not success:
                    logger.error("FEHLER beim Akku-Stopp")
                return success
            
            # Leistung muss immer positiv sein für die Verteilungsfunktion
            power_abs = abs(total_power)

            success = self.batteries.distribute_power(
                total_power=power_abs,
                mode=mode,
                min_soc=self.min_soc_discharge,
                max_soc=self.max_soc_charge
            )
            
            # Reduziertes Logging - nur bei Fehlern interessant
            if not success:
                mode_text = "LADEN" if mode == 1 else "ENTLADEN"
                logger.error(f"FEHLER beim {mode_text} mit {power_abs:.0f}W")
            
            return success
            
        except Exception as e:
            logger.error(f"Fehler bei Akku-Steuerung: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'current_mode': self.current_mode,
            'mode_text': {0: 'Stop', 1: 'Laden', 2: 'Entladen'}.get(self.current_mode, 'Unbekannt'),
            'current_total_power': self.current_total_power,
            'last_grid_power': self.last_grid_power,
            'mode_change_count': self.mode_change_count,
            'target_grid_charge': self.target_grid_power_charge,
            'target_grid_discharge': self.target_grid_power_discharge,
            'max_power_change_rate': self.max_power_change_rate,
            'low_soc_protection': {
                'threshold': self.low_soc_threshold,
                'min_surplus': self.low_soc_min_surplus
            }
        }
    
    def reset_statistics(self):
        self.mode_change_count = 0
        logger.info("Controller-Statistiken zurückgesetzt")