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
import math
from cosapp.base import System
from models.vehicle_port import VehiclePropertiesPort

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# 1. VEHICLE CAPEX CALCULATOR
# ============================================================================

class VehicleCAPEXCalculator(System):
    """CAPEX calculation system for vehicles."""
    
    def setup(self, db_path: str = "db_trucks.json"):
        # -------------------- LOAD DATABASE --------------------
        full_db_path = os.path.join(BASE_DIR, db_path) if not os.path.isabs(db_path) else db_path
        with open(full_db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
        
        # Build country index
        countries_dict = {}
        for country_entry in db_data.get("countries", []):
            country_name = country_entry.get("country")
            countries_dict[country_name] = country_entry.get("data_country", {})
        
        object.__setattr__(self, "_db", db_data)
        object.__setattr__(self, "_countries", countries_dict)
        
        # -------------------- PORTS --------------------
        self.add_input(VehiclePropertiesPort, 'in_vehicle_properties')
        
        # -------------------- OUTPUTS --------------------
        self.add_outward("c_infrastructure_hardware", 0.0)
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
    
    def get_country_data(self):
        """Get country-specific data."""
        vp = self.in_vehicle_properties
        return self._countries.get(vp.country, {})
    
    def get_charger_params(self, charger_type: str):
        """Get charger parameters from database."""
        country_data = self.get_country_data()
        return country_data.get('infrastructure', {}).get('chargers', {}).get(charger_type, {})
    
    def get_station_params(self, station_type: str):
        """Get station parameters from database."""
        country_data = self.get_country_data()
        return country_data.get('infrastructure', {}).get('stations', {}).get(station_type, {})
    
    def get_grid_cost(self, total_power_kw: float) -> float:
        """Calculate grid connection cost based on total power."""
        country_data = self.get_country_data()
        tiers = country_data.get('infrastructure', {}).get('grid_connection', {}).get('tiers', [])
        for tier in tiers:
            if total_power_kw <= tier.get('max_power_kw', 0):
                return tier.get('cost_eur', 0.0)
        return tiers[-1].get('cost_eur', 0.0) if tiers else 0.0
    
    def get_software_cost(self) -> float:
        """Get software cost based on powertrain type."""
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        software = country_data.get('infrastructure', {}).get('software', {})
        
        if vp.type_energy in ['bet', 'phev']:
            base = software.get('bet', {}).get('base_cost_eur', 0.0)
            if vp.smart_charging_enabled:
                base += software.get('bet', {}).get('load_management_addon_eur', 0.0)
            return base
        elif vp.type_energy in ['fcet', 'hice']:
            return software.get('fcet', {}).get('hice_monitoring_cost_eur', 0.0)
        elif vp.type_energy in ['gnv', 'lng']:
            return software.get('gnv', {}).get('gas_monitoring_cost_eur', 0.0)
        return 0.0
    
    def get_taxes_params(self):
        """Get tax parameters from database."""
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        taxes = country_data.get('taxes_registration', {})
        return taxes.get(vp.vehicle_weight_class, {}).get(vp.type_energy, 0.0)
    
    def get_subsidies_params(self):
        """Get subsidy parameters from database."""
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        subsidies = country_data.get('subsidies', {})
        year_data = subsidies.get(str(vp.year), {})
        weight_data = year_data.get(vp.vehicle_weight_class, {})
        return weight_data.get(vp.type_energy, {})
    
    def get_financing_params(self):
        """Get financing parameters from database."""
        country_data = self.get_country_data()
        return country_data.get('financing', {})

    # ==================== FLEET ENERGY CALCULATION ====================
    
    def compute_fleet_energy(self):
        """Calculate total energy consumption for the fleet."""
        vp = self.in_vehicle_properties
        self.E_total_slow = 0.0
        self.E_total_fast = 0.0
        self.E_total_ultra = 0.0
        self.E_total_private = 0.0
        
        if vp.type_energy in ['bet', 'phev']:
            for vid, vdata in vp.vehicle_dict.items():
                E = vdata.get('E_t', 0.0)
                S = vdata.get('Private_S_t', 0.0)
                F = vdata.get('Private_F_t', 0.0)   
                U = vdata.get('Private_U_t', 0.0)
                
                self.E_total_slow += E * S
                self.E_total_fast += E * F
                self.E_total_ultra += E * U
        else:
            for vid, vdata in vp.vehicle_dict.items():
                E = vdata.get('E_t', 0.0)
                P = vdata.get('Private_t', 0.0)
                self.E_total_private += E * P

    # ==================== C_VEHICLE_COST ====================
    
    def compute_c_vehicle_cost(self):
        """Calculate vehicle acquisition cost."""
        vp = self.in_vehicle_properties
        if vp.is_new:
            self.c_vehicle_cost = vp.purchase_cost
        elif vp.owns_vehicle:
            self.c_vehicle_cost = vp.conversion_cost + vp.certification_cost
        else:
            self.c_vehicle_cost = vp.purchase_cost + vp.conversion_cost + vp.certification_cost

    # ==================== C_INFRASTRUCTURE_COST ====================
    
    def compute_c_infrastructure_cost(self):
        """Calculate infrastructure cost per vehicle."""
        vp = self.in_vehicle_properties
        if vp.type_energy in ['bet', 'phev']:
            self._compute_charging_infrastructure()
        else:
            self._compute_fueling_infrastructure()
        
        # Software cost
        software_cost = self.get_software_cost() / vp.vehicle_number
        
        # Site preparation
        country_data = self.get_country_data()
        site_cost = country_data.get('infrastructure', {}).get('site_preparation', {}).get(
            vp.type_energy, {}
        ).get('cost_eur', 0.0) / vp.vehicle_number
        
        # Safety
        n_stations_calc = vp.n_stations if vp.n_stations else 1
        safety_data = country_data.get('infrastructure', {}).get('safety', {}).get(vp.type_energy, {})
        if 'cost_per_station_eur' in safety_data:
            safety_cost = safety_data['cost_per_station_eur'] * n_stations_calc
        elif 'cost_total_eur' in safety_data:
            safety_cost = safety_data['cost_total_eur']
        else:
            safety_cost = 0.0
        safety_cost = safety_cost / vp.vehicle_number
        
        # Licensing
        country_data = self.get_country_data()
        licensing_cost = country_data.get('licensing', {}).get(vp.type_energy, 0.0) / vp.vehicle_number
        
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
        vp = self.in_vehicle_properties
        slow_params = self.get_charger_params('slow')
        fast_params = self.get_charger_params('fast')
        ultra_params = self.get_charger_params('ultra')
        
        # Calculate number of chargers if not specified
        if vp.n_slow is None and vp.n_fast is None and vp.n_ultra is None:
            H_demand_slow = (self.E_total_slow / 
                           (slow_params.get('power_kw', 1) * slow_params.get('charging_efficiency', 0.95)) 
                           if self.E_total_slow > 0 else 0)
            H_demand_fast = (self.E_total_fast / 
                           (fast_params.get('power_kw', 1) * fast_params.get('charging_efficiency', 0.95)) 
                           if self.E_total_fast > 0 else 0)
            H_demand_ultra = (self.E_total_ultra / 
                            (ultra_params.get('power_kw', 1) * ultra_params.get('charging_efficiency', 0.95)) 
                            if self.E_total_ultra > 0 else 0)
            
            H_cap_slow = slow_params.get('operating_hours_per_day', 20) * slow_params.get('operating_days_per_year', 365)
            H_cap_fast = fast_params.get('operating_hours_per_day', 20) * fast_params.get('operating_days_per_year', 365)
            H_cap_ultra = ultra_params.get('operating_hours_per_day', 20) * ultra_params.get('operating_days_per_year', 365)
            
            self.n_slow_calculated = int(math.ceil(H_demand_slow / H_cap_slow)) if H_demand_slow > 0 else 0
            self.n_fast_calculated = int(math.ceil(H_demand_fast / H_cap_fast)) if H_demand_fast > 0 else 0
            self.n_ultra_calculated = int(math.ceil(H_demand_ultra / H_cap_ultra)) if H_demand_ultra > 0 else 0
        else:
            self.n_slow_calculated = vp.n_slow or 0
            self.n_fast_calculated = vp.n_fast or 0
            self.n_ultra_calculated = vp.n_ultra or 0
        
        # Calculate shares for this vehicle
        vdata = vp.vehicle_dict.get(str(vp.vehicle_id), {})
        E = vdata.get('E_t', 0.0)   
        S = vdata.get('Private_S_t', 0.0)
        F = vdata.get('Private_F_t', 0.0)
        U = vdata.get('Private_U_t', 0.0)
        share_slow = (E * S / self.E_total_slow) if self.E_total_slow > 0 else 0
        share_fast = (E * F / self.E_total_fast) if self.E_total_fast > 0 else 0
        share_ultra = (E * U / self.E_total_ultra) if self.E_total_ultra > 0 else 0 
        
        # Hardware cost
        self.c_infrastructure_hardware = (
            self.n_slow_calculated * slow_params.get('price_eur', 0) * share_slow +
            self.n_fast_calculated * fast_params.get('price_eur', 0) * share_fast +
            self.n_ultra_calculated * ultra_params.get('price_eur', 0) * share_ultra
        )
        
        # Grid connection
        total_power = (
            self.n_slow_calculated * slow_params.get('power_kw', 0) +
            self.n_fast_calculated * fast_params.get('power_kw', 0) +
            self.n_ultra_calculated * ultra_params.get('power_kw', 0)
        )
        grid_cost_total = self.get_grid_cost(total_power)
        vehicle_power = (
            self.n_slow_calculated * slow_params.get('power_kw', 0) * share_slow +
            self.n_fast_calculated * fast_params.get('power_kw', 0) * share_fast +
            self.n_ultra_calculated * ultra_params.get('power_kw', 0) * share_ultra
        )
        contribution = vehicle_power / total_power if total_power > 0 else 0
        self.c_infrastructure_grid = grid_cost_total * contribution
        
        # Installation
        self.c_infrastructure_installation = (
            self.n_slow_calculated * slow_params.get('installation_cost_eur', 0) * share_slow +
            self.n_fast_calculated * fast_params.get('installation_cost_eur', 0) * share_fast +
            self.n_ultra_calculated * ultra_params.get('installation_cost_eur', 0) * share_ultra
        )
    
    def _compute_fueling_infrastructure(self):
        """Compute fueling infrastructure for non-electric vehicles."""
        vp = self.in_vehicle_properties
        # Determine station type
        if vp.type_energy in ['diesel', 'biodiesel', 'hvo', 'e_diesel', 'hev']:
            station_type = 'diesel'
        elif vp.type_energy in ['fcet', 'hice']:
            station_type = 'hice'
        elif vp.type_energy == 'gnv':
            station_type = 'gnv'
        elif vp.type_energy == 'lng':
            station_type = 'lng'
        else:
            station_type = 'diesel'
        
        station_params = self.get_station_params(station_type)
        n_stations_calc = vp.n_stations if vp.n_stations else 1
        vdata = vp.vehicle_dict.get(str(vp.vehicle_id), {})
        E = vdata.get('E_t', 0.0)   
        P = vdata.get('Private_t', 0.0)
        share_private = (E * P / self.E_total_private) if self.E_total_private > 0 else 0
      
        # Hardware
        self.c_infrastructure_hardware = station_params.get('hardware_cost_per_station_eur', 0.0) * share_private * n_stations_calc 
        
        # Grid connection
        if station_type == 'hice':
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
            vp.vehicle_number
        )

    # ==================== C_TAXES ====================
    
    def compute_c_taxes(self):
        """Calculate registration taxes."""
        self.c_taxes = self.get_taxes_params()

    # ==================== C_SUBSIDIES ====================
    
    def compute_c_subsidies(self):
        """Calculate total subsidies (vehicle + infrastructure)."""
        vp = self.in_vehicle_properties
        subsidies_params = self.get_subsidies_params()
        
        # Vehicle subsidy
        vehicle_subsidy = subsidies_params.get('vehicle_subsidy', 0.0)
        
        # Infrastructure subsidy
        infra_rate = subsidies_params.get('infrastructure_subsidy_rate', 0.0)
        infrastructure_subsidy = self.c_infrastructure_cost * infra_rate
        
        self.c_subsidies = vehicle_subsidy + (infrastructure_subsidy / vp.vehicle_number)

    # ==================== C_FINANCING_COST ====================
    
    def compute_c_financing_cost(self):
        """Calculate financing cost and CRF."""
        vp = self.in_vehicle_properties
        fin_params = self.get_financing_params()
        
        base_rate = fin_params.get('base_interest_rate', 0.04)
        esg_adjustments = fin_params.get('esg_adjustments', {})
        esg_adjustment = esg_adjustments.get(vp.type_energy, 0.0)
        adjusted_rate = base_rate + esg_adjustment
        
        # Origination fee
        origination_rate = fin_params.get('origination_fee_rate', 0.01)
        self.c_financing_cost = self.c_vehicle_cost * origination_rate
        
        # CRF calculation
        r = adjusted_rate
        n = vp.loan_years
        if r > 0:
            self.c_crf = (r * (1 + r)**n) / ((1 + r)**n - 1)
        else:
            self.c_crf = 1.0

    # ==================== MAIN COMPUTE ====================
    
    def compute(self):
        """Main compute method for vehicle CAPEX."""
        
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

