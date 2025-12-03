"""
CosApp System for calculating vehicle CAPEX costs using external database and json outputs

===============================================================================
MODULE STRUCTURE :  
DATABASE PARAMETERS (Retrieved automatically)
   - Country parameters, financing rates, subsidies, tax rates
   
USER INPUTS (Must be provided)
   - Vehicle characteristics, fleet size, energy consumption
   
 SYSTEM OUTPUTS (Calculated results)
   - Vehicle_Cost, Infrastructure_Cost, Taxes, Financing, Subsidies, Total_CAPEX
"""

import json
import sys
import os
from cosapp.drivers import RunOnce
from cosapp.base import System
from cosapp.ports import Port
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# 0. VEHICLE TYPES MAPPING
# ============================================================================
POWERTRAIN_TYPES = [
    'bet', 'phev', 'fcet', 'hice', 'gnv', 'lng',
    'diesel', 'biodiesel', 'hvo', 'e_diesel'
]

VEHICLE_WEIGHT_CLASSES = ['light', 'medium', 'heavy']


# ============================================================================
# 1. PORT FOR VEHICLE CAPEX (ORANGE + GREEN)
# ============================================================================

class VehicleCAPEXPort(Port):
    """Port for CAPEX calculation inputs and outputs for vehicles."""

    def setup(self):
        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_variable("powertrain_type", dtype=str, desc="Type of powertrain (bet, diesel, etc.)")
        self.add_variable("vehicle_number", dtype=int, desc="Number of vehicles in fleet")
        self.add_variable("vehicle_id", dtype=int, desc="Vehicle ID in fleet")
        self.add_variable("vehicle_weight_class", dtype=str, desc="Weight class (light/medium/heavy)")
        self.add_variable("country", dtype=str, desc="Country code (EU, France, etc.)")
        self.add_variable("year", dtype=int, desc="Year for subsidies calculation")
        
        # Vehicle acquisition
        self.add_variable("is_new", dtype=bool, desc="True if buying new vehicle")
        self.add_variable("owns_vehicle", dtype=bool, desc="True if already owns vehicle")
        self.add_variable("purchase_price", dtype=float, desc="Purchase price in EUR")
        self.add_variable("conversion_cost", dtype=float, desc="Conversion cost in EUR")
        self.add_variable("certification_cost", dtype=float, desc="Certification cost in EUR")
        
        # Energy and infrastructure
        #self.add_variable("E_t", dtype=float, desc="Annual energy consumption (kWh)")
        #self.add_variable("S_t", dtype=float, desc="Share of slow charging")
        #self.add_variable("F_t", dtype=float, desc="Share of fast charging")
        #self.add_variable("U_t", dtype=float, desc="Share of ultra-fast charging")
        #self.add_variable("Public_t", dtype=float, desc="Share of public charging")
        #self.add_variable("Private_t", dtype=float, desc="Share of private charging")
        self.add_variable("vehicle_dict",{},
                        desc="Dictionary of vehicles: " \
                        "- for electric :{id: {E_t, Private_S_t, Private_F_t, Private_U_t, Public_S_t,Public_F_t,Public_U_t}}"
                        "- for non-electric :{id: {E_t, Private_t, Public_t}}")
                
        # Infrastructure parameters
        self.add_variable("n_slow", dtype=int, desc="Number of slow chargers (optional)")
        self.add_variable("n_fast", dtype=int, desc="Number of fast chargers (optional)")
        self.add_variable("n_ultra", dtype=int, desc="Number of ultra-fast chargers (optional)")
        self.add_variable("n_stations", dtype=int, desc="Number of stations (optional)")
        self.add_variable("smart_charging_enabled", dtype=bool, desc="Smart charging enabled")
        
        # Financing
        self.add_variable("loan_years", dtype=int, desc="Number of years for loan")
        
        # -------------------- OUTPUTS (GREEN) --------------------
        self.add_variable("c_vehicle_cost", dtype=float, desc="Vehicle acquisition cost in EUR")
        self.add_variable("c_infrastructure_cost", dtype=float, desc="Infrastructure cost in EUR")
        self.add_variable("c_taxes", dtype=float, desc="Registration taxes in EUR")
        self.add_variable("c_financing_cost", dtype=float, desc="Financing cost in EUR")
        self.add_variable("c_subsidies", dtype=float, desc="Total subsidies in EUR")
        self.add_variable("c_capex_total", dtype=float, desc="Total CAPEX in EUR")
        self.add_variable("c_capex_per_vehicle", dtype=float, desc="CAPEX per vehicle per year in EUR")
        self.add_variable("c_crf", dtype=float, desc="Capital Recovery Factor")


# ============================================================================
# 2. VEHICLE CAPEX COSAPP SYSTEM
# ============================================================================

class VehicleCAPEXCalculator(System):
    """CAPEX calculation system for vehicles following OPEX structure."""
    
    def setup(self, db_path: str = "database.json"):
        # -------------------- LOAD DATABASE (YELLOW) --------------------
        full_db_path = os.path.join(BASE_DIR, db_path) if not os.path.isabs(db_path) else db_path
        with open(full_db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
        
        object.__setattr__(self, "_db", db_data)
        
        # -------------------- PORT (ORANGE+GREEN) --------------------
        self.add_inward("capex_vehicle", VehicleCAPEXPort, desc="CAPEX calculation port")
        
        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_inward("powertrain_type", "bet", dtype=str)
        self.add_inward("vehicle_number", 1, dtype=int)
        self.add_inward("vehicle_id", 1, dtype=int)
        self.add_inward("vehicle_weight_class", "heavy", dtype=str)
        self.add_inward("country", "EU", dtype=str)
        self.add_inward("year", 2025, dtype=int)
        
        # Vehicle acquisition
        self.add_inward("is_new", True, dtype=bool)
        self.add_inward("owns_vehicle", False, dtype=bool)
        self.add_inward("purchase_price", 80000.0, dtype=float)
        self.add_inward("conversion_cost", 0.0, dtype=float)
        self.add_inward("certification_cost", 0.0, dtype=float)
        
        # Energy consumption
        #self.add_inward("E_t", 15000.0, dtype=float)
        #self.add_inward("S_t", 0.3, dtype=float)
        #self.add_inward("F_t", 0.4, dtype=float)
        #self.add_inward("U_t", 0.1, dtype=float)
        #self.add_inward("Public_t", 0.2, dtype=float)
        #self.add_inward("Private_t", 0.0, dtype=float)
        
        # Infrastructure
        self.add_inward("n_slow", None)
        self.add_inward("n_fast", None)
        self.add_inward("n_ultra", None)
        self.add_inward("n_stations", None)
        self.add_inward("smart_charging_enabled", False, dtype=bool)
        
        # Fleet dictionary for shared infrastructure
        self.add_inward("vehicle_dict",{},
                        desc="Dictionary of vehicles: " \
                        "- for electric :{id: {E_t, Private_S_t, Private_F_t, Private_U_t, Public_S_t,Public_F_t,Public_U_t}}"
                        "- for non-electric :{id: {E_t, Private_t, Public_t}}")
                
        # Financing
        self.add_inward("loan_years", 10, dtype=int)
        
        # -------------------- OUTPUTS (GREEN) --------------------
        self.add_outward("c_infrastructure_hardware",0)
        self.add_outward("c_infrastructure_grid", 0.0)
        self.add_outward("c_infrastructure_installation", 0.0)

        self.add_outward("c_vehicle_cost", 0.0)
        self.add_outward("c_infrastructure_cost", 0.0)
        self.add_outward("c_taxes", 0.0)
        self.add_outward("c_financing_cost", 0.0)
        self.add_outward("c_subsidies", 0.0)
        self.add_outward("c_capex_total", 0.0)
        self.add_outward("c_capex_per_vehicle", 0.0)
        self.add_outward("c_crf", 1.0)
        
        # Intermediate outputs
        self.add_outward("n_slow_calculated", 0, dtype=int)
        self.add_outward("n_fast_calculated", 0, dtype=int)
        self.add_outward("n_ultra_calculated", 0, dtype=int)
        self.add_outward("E_total_slow", 0.0)
        self.add_outward("E_total_fast", 0.0)
        self.add_outward("E_total_ultra", 0.0)
        self.add_outward("E_total_private", 0.0)

    # ==================== DATABASE ACCESS METHODS ====================
    
    def get_charger_params(self, charger_type: str):
        """Get charger parameters from database."""
        return self._db['infrastructure']['chargers'].get(charger_type, {})
    
    def get_station_params(self, station_type: str):
        """Get station parameters from database."""
        return self._db['infrastructure']['stations'].get(station_type, {})
    
    def get_grid_cost(self, total_power_kw: float) -> float:
        """Calculate grid connection cost based on total power."""
        tiers = self._db['infrastructure']['grid_connection']['tiers']
        for tier in tiers:
            if total_power_kw <= tier['max_power_kw']:
                return tier['cost_eur']
        return tiers[-1]['cost_eur']
    
    def get_software_cost(self) -> float:
        """Get software cost based on powertrain type."""
        software = self._db['infrastructure']['software']
        if self.powertrain_type in ['bet', 'phev']:
            base = software['bet']['base_cost_eur']
            if self.smart_charging_enabled:
                base += software['bet']['load_management_addon_eur']
            return base
        elif self.powertrain_type in ['fcet', 'hice']:
            return software['fcet']['h2_monitoring_cost_eur']
        elif self.powertrain_type in ['gnv', 'lng']:
            return software['gnv']['gas_monitoring_cost_eur']
        return 0.0
    
    def get_taxes_params(self):
        """Get tax parameters from database."""
        try:
            return self._db['taxes'][self.country][self.vehicle_weight_class][self.powertrain_type]
        except KeyError:
            return {'registration': 0.0, 'specific': 0.0}
    
    def get_subsidies_params(self):
        """Get subsidy parameters from database."""
        try:
            return self._db['subsidies'][self.country][str(self.year)][self.vehicle_weight_class][self.powertrain_type]
        except KeyError:
            return {}
    
    def get_financing_params(self):
        """Get financing parameters from database."""
        return self._db['financing']

    # ==================== FLEET ENERGY CALCULATION ====================
    
    def compute_fleet_energy(self):
        """Calculate total energy consumption for the fleet."""
        self.E_total_slow = 0.0
        self.E_total_fast = 0.0
        self.E_total_ultra = 0.0
        self.E_total_private = 0.0
        
        if self.powertrain_type not in ['bet', 'phev']:
            for vid, vdata in self.vehicle_dict.items():
                E = vdata.get('E_t', 0.0)
                S = vdata.get('Private_S_t', 0.0)
                F = vdata.get('Private_F_t', 0.0)   
                U = vdata.get('Private_U_t', 0.0)

                
                self.E_total_slow += E * S
                self.E_total_fast += E * F
                self.E_total_ultra += E * U
        else:
            for vid, vdata in self.vehicle_dict.items():
                E = vdata.get('E_t', 0.0)
                P= vdata.get('Private_t', 0.0)
                self.E_total_private += E * P

        



    # ==================== C_VEHICLE_COST ====================
    
    def compute_c_vehicle_cost(self):
        """
        Calculate vehicle acquisition cost.
        c_vehicle_cost = purchase_price (if new)
                       OR conversion_cost + certification_cost (if owns)
                       OR purchase_price + conversion + certification (if used)
        """
        if self.is_new:
            self.c_vehicle_cost = self.purchase_price
        elif self.owns_vehicle:
            self.c_vehicle_cost = self.conversion_cost + self.certification_cost
        else:
            self.c_vehicle_cost = self.purchase_price + self.conversion_cost + self.certification_cost

    # ==================== C_INFRASTRUCTURE_COST ====================
    
    def compute_c_infrastructure_cost(self):
        """
        Calculate infrastructure cost per vehicle.
        Components:
        - Hardware (chargers or stations)
        - Software
        - Grid connection
        - Installation
        - Site preparation
        - Safety
        - Licensing
        """

        if self.powertrain_type in ['bet', 'phev']:
            self._compute_charging_infrastructure()
        else:
            self._compute_fueling_infrastructure()
        
        # Software cost
        software_cost = self.get_software_cost() / self.vehicle_number
        
        # Site preparation
        site_cost = self._db['infrastructure']['site_preparation'].get(
            self.powertrain_type, {}
        ).get('cost_eur', 0.0) / self.vehicle_number
        
        # Safety
        n_stations_calc = self.n_stations if self.n_stations else 1
        safety_data = self._db['infrastructure']['safety'].get(self.powertrain_type, {})
        if 'cost_per_station_eur' in safety_data:
            safety_cost = safety_data['cost_per_station_eur'] * n_stations_calc
        elif 'cost_total_eur' in safety_data:
            safety_cost = safety_data['cost_total_eur']
        else:
            safety_cost = 0.0
        safety_cost = safety_cost / self.vehicle_number
        
        # Licensing
        licensing_cost = self._db['infrastructure']['licensing'].get(
            self.country, {}
        ).get(self.powertrain_type, 0.0) / self.vehicle_number
        
        # Total infrastructure
        self.c_infrastructure_cost = (
            self.c_infrastructure_hardware +
            software_cost +
            self.c_infrastructure_grid +
            self.c_infrastructure_installation +
            site_cost +
            safety_cost +
            licensing_cost
        )
    
    def _compute_charging_infrastructure(self):
        """Compute charging infrastructure for BET/PHEV."""
        slow_params = self.get_charger_params('slow')
        fast_params = self.get_charger_params('fast')
        ultra_params = self.get_charger_params('ultra')
        
        # Calculate number of chargers if not specified
        if self.n_slow is None and self.n_fast is None and self.n_ultra is None:
            H_demand_slow = (self.E_total_slow / 
                           (slow_params['power_kw'] * slow_params['charging_efficiency']) 
                           if self.E_total_slow > 0 else 0)
            H_demand_fast = (self.E_total_fast / 
                           (fast_params['power_kw'] * fast_params['charging_efficiency']) 
                           if self.E_total_fast > 0 else 0)
            H_demand_ultra = (self.E_total_ultra / 
                            (ultra_params['power_kw'] * ultra_params['charging_efficiency']) 
                            if self.E_total_ultra > 0 else 0)
            
            H_cap_slow = slow_params['operating_hours_per_day'] * slow_params['operating_days_per_year']
            H_cap_fast = fast_params['operating_hours_per_day'] * fast_params['operating_days_per_year']
            H_cap_ultra = ultra_params['operating_hours_per_day'] * ultra_params['operating_days_per_year']
            
            self.n_slow_calculated = int(np.ceil(H_demand_slow / H_cap_slow)) if H_demand_slow > 0 else 0
            self.n_fast_calculated = int(np.ceil(H_demand_fast / H_cap_fast)) if H_demand_fast > 0 else 0
            self.n_ultra_calculated = int(np.ceil(H_demand_ultra / H_cap_ultra)) if H_demand_ultra > 0 else 0
        else:
            self.n_slow_calculated = self.n_slow or 0
            self.n_fast_calculated = self.n_fast or 0
            self.n_ultra_calculated = self.n_ultra or 0
        
        # Calculate shares for this vehicle
        #share_slow = (self.E_t * self.S_t / self.E_total_slow) if self.E_total_slow > 0 else 0
        #share_fast = (self.E_t * self.F_t / self.E_total_fast) if self.E_total_fast > 0 else 0
        #share_ultra = (self.E_t * self.U_t / self.E_total_ultra) if self.E_total_ultra > 0 else 0
        vdata = self.vehicle_dict.get(str(self.vehicle_id), {})
        E = vdata.get('E_t', 0.0)   
        S = vdata.get('S_t', 0.0)
        F = vdata.get('F_t', 0.0)
        U = vdata.get('U_t', 0.0)
        share_slow = (E * S / self.E_total_slow) if self.E_total_slow > 0 else 0
        share_fast = (E * F / self.E_total_fast) if self.E_total_fast > 0 else 0
        share_ultra = (E * U / self.E_total_ultra) if self.E_total_ultra > 0 else 0 
        
        # Hardware cost
        self.c_infrastructure_hardware = (
            self.n_slow_calculated * slow_params['price_eur'] * share_slow +
            self.n_fast_calculated * fast_params['price_eur'] * share_fast +
            self.n_ultra_calculated * ultra_params['price_eur'] * share_ultra
        )
        
        # Grid connection
        total_power = (
            self.n_slow_calculated * slow_params['power_kw'] +
            self.n_fast_calculated * fast_params['power_kw'] +
            self.n_ultra_calculated * ultra_params['power_kw']
        )
        grid_cost_total = self.get_grid_cost(total_power)
        vehicle_power = (
            self.n_slow_calculated * slow_params['power_kw'] * share_slow +
            self.n_fast_calculated * fast_params['power_kw'] * share_fast +
            self.n_ultra_calculated * ultra_params['power_kw'] * share_ultra
        )
        contribution = vehicle_power / total_power if total_power > 0 else 0
        self.c_infrastructure_grid = grid_cost_total * contribution
        
        # Installation
        self.c_infrastructure_installation = (
            self.n_slow_calculated * slow_params['installation_cost_eur'] * share_slow +
            self.n_fast_calculated * fast_params['installation_cost_eur'] * share_fast +
            self.n_ultra_calculated * ultra_params['installation_cost_eur'] * share_ultra
        )
    
    def _compute_fueling_infrastructure(self):
        """Compute fueling infrastructure for non-electric vehicles."""
        # Determine station type
        if self.powertrain_type in ['diesel', 'biodiesel', 'hvo', 'e_diesel', 'hev']:
            station_type = 'diesel'
        elif self.powertrain_type in ['fcet', 'hice']:
            station_type = 'h2'
        elif self.powertrain_type == 'gnv':
            station_type = 'gnv'
        elif self.powertrain_type == 'lng':
            station_type = 'lng'
        else:
            station_type = 'diesel'
        
        station_params = self.get_station_params(station_type)
        n_stations_calc = self.n_stations if self.n_stations else 1
        vdata = self.vehicle_dict.get(str(self.vehicle_id), {})
        E = vdata.get('E_t', 0.0)   
        P = vdata.get('Private_t', 0.0)
        share_private = (E * P / self.E_total_private) if self.E_total_private > 0 else 0
      
        # Hardware
        self.c_infrastructure_hardware =  station_params.get('hardware_cost_per_station_eur', 0.0) * share_private * n_stations_calc 
        
        
        # Grid connection
        if station_type == 'h2':
            self.c_infrastructure_grid = (
                n_stations_calc * 
                station_params.get('electrolyzer_grid_connection_cost_eur', 0.0) * share_private
            )
        elif station_type in ['gnv', 'lng']:
            self.c_infrastructure_grid = (
                n_stations_calc * 
                station_params.get('electricity_connection_cost_eur', 0.0) * share_private
            )
        else:
            self.c_infrastructure_grid = 0.0
        
        # Installation
        self.c_infrastructure_installation = (
            n_stations_calc * 
            station_params.get('installation_cost_per_station_eur', 
                             station_params.get('installation_cost_per_pump_eur', 0.0)) / 
            self.vehicle_number )

    # ==================== C_TAXES ====================
    
    def compute_c_taxes(self):
        """Calculate registration taxes."""
        taxes_params = self.get_taxes_params()
        self.c_taxes = taxes_params.get('registration', 0.0)

    # ==================== C_SUBSIDIES ====================
    
    def compute_c_subsidies(self):
        """
        Calculate total subsidies (vehicle + infrastructure).
        """
        subsidies_params = self.get_subsidies_params()
        
        # Vehicle subsidy
        vehicle_subsidy = 0.0
        if 'vehicle_subsidy_thresholds' in subsidies_params:
            for threshold in subsidies_params['vehicle_subsidy_thresholds']:
                if self.c_vehicle_cost <= threshold['max_purchase_price']:
                    vehicle_subsidy = threshold['subsidy']
                    break
        elif 'vehicle_subsidy' in subsidies_params:
            vehicle_subsidy = subsidies_params['vehicle_subsidy']
        
        # Infrastructure subsidy
        infra_rate = subsidies_params.get('infrastructure_subsidy_rate', 0.0)
        infrastructure_subsidy = self.c_infrastructure_cost * infra_rate
        
        self.c_subsidies = vehicle_subsidy + (infrastructure_subsidy / self.vehicle_number)

    # ==================== C_FINANCING_COST ====================
    
    def compute_c_financing_cost(self):
        """
        Calculate financing cost and CRF (Capital Recovery Factor).
        CRF = [r(1+r)^n] / [(1+r)^n - 1]
        """
        fin_params = self.get_financing_params()
        
        base_rate = fin_params['base_interest_rate']
        esg_adjustment = fin_params['esg_adjustments'].get(self.powertrain_type, 0.0)
        adjusted_rate = base_rate + esg_adjustment
        
        # Origination fee
        origination_rate = fin_params['origination_fee_rate']
        self.c_financing_cost = self.c_vehicle_cost * origination_rate
        
        # CRF calculation
        r = adjusted_rate
        n = self.loan_years
        if r > 0:
            self.c_crf = (r * (1 + r)**n) / ((1 + r)**n - 1)
        else:
            self.c_crf = 1.0

    # ==================== MAIN COMPUTE ====================
    
    def compute(self):
        """
        Main compute method for vehicle CAPEX:
        CAPEX = Vehicle_Cost + Infrastructure_Cost + Taxes + Financing - Subsidies
        CAPEX_per_vehicle = CAPEX_total × CRF
        """
        p = self.capex_vehicle
        
        # Calculate fleet energy totals
        self.compute_fleet_energy()
        
        # Calculate each component
        self.compute_c_vehicle_cost()
        self.compute_c_infrastructure_cost()
        self.compute_c_taxes()
        self.compute_c_subsidies()
        self.compute_c_financing_cost()
        
        # Total CAPEX
        self.c_capex_total = (
            self.c_vehicle_cost +
            self.c_infrastructure_cost +
            self.c_taxes +
            self.c_financing_cost -
            self.c_subsidies
        )
        
        # CAPEX per year
        self.c_capex_per_vehicle = self.c_capex_total * self.c_crf
        
        # Populate port outputs
        p.powertrain_type = self.powertrain_type
        p.vehicle_number = self.vehicle_number
        p.vehicle_id = self.vehicle_id
        p.vehicle_weight_class = self.vehicle_weight_class
        p.country = self.country
        p.year = self.year
        
        p.is_new = self.is_new
        p.owns_vehicle = self.owns_vehicle
        p.purchase_price = self.purchase_price
        p.conversion_cost = self.conversion_cost
        p.certification_cost = self.certification_cost
        
        #p.E_t = self.E_t
        #p.S_t = self.S_t
        #p.F_t = self.F_t
        #p.U_t = self.U_t
        #p.Public_t = self.Public_t
        #p.Private_t = self.Private_t
        
        p.n_slow = self.n_slow
        p.n_fast = self.n_fast
        p.n_ultra = self.n_ultra
        p.n_stations = self.n_stations
        p.smart_charging_enabled = self.smart_charging_enabled
        
        p.loan_years = self.loan_years
        
        p.c_vehicle_cost = self.c_vehicle_cost
        p.c_infrastructure_cost = self.c_infrastructure_cost
        p.c_taxes = self.c_taxes
        p.c_financing_cost = self.c_financing_cost
        p.c_subsidies = self.c_subsidies
        p.c_capex_total = self.c_capex_total
        p.c_capex_per_vehicle = self.c_capex_per_vehicle
        p.c_crf = self.c_crf
