"""
CAPEX Calculation System using CoSApp Framework
Structured with separate classes: Vehicle, Infrastructure, Taxes, Subsidies, Financing, CAPEX
All parameters loaded from database.json
"""

from cosapp.base import System
from cosapp.drivers import RunOnce
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any


# =============================================================================
# DATABASE LOADER
# =============================================================================

class DatabaseLoader:
    """Loads and validates all parameters from database.json"""
    
    def __init__(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        self.db_path = Path(db_path)
        self.db = self.load_database()
        
    def load_database(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_input(self, key: str, value: Any) -> bool:
        valid_values = self.db['valid_values']
        if key == 'powertrain_type':
            return value in valid_values['powertrain_types']
        elif key == 'country':
            return value in valid_values['countries']
        elif key == 'vehicle_weight_class':
            return value in valid_values['vehicle_weight_classes']
        return True
    
    def get_charger_params(self, charger_type: str) -> Dict[str, Any]:
        return self.db['infrastructure']['chargers'].get(charger_type, {})
    
    def get_station_params(self, station_type: str) -> Dict[str, Any]:
        return self.db['infrastructure']['stations'].get(station_type, {})
    
    def get_grid_cost(self, total_power_kw: float) -> float:
        tiers = self.db['infrastructure']['grid_connection']['tiers']
        for tier in tiers:
            if total_power_kw <= tier['max_power_kw']:
                return tier['cost_eur']
        return tiers[-1]['cost_eur']
    
    def get_software_cost(self, powertrain_type: str, smart_charging: bool = False) -> float:
        software = self.db['infrastructure']['software']
        if powertrain_type in ['bet', 'phev']:
            base = software['bet']['base_cost_eur']
            if smart_charging:
                base += software['bet']['load_management_addon_eur']
            return base
        elif powertrain_type in ['fcet', 'hice']:
            return software['fcet']['h2_monitoring_cost_eur']
        elif powertrain_type in ['gnv', 'lng']:
            return software['gnv']['gas_monitoring_cost_eur']
        return 0.0
    
    def get_site_cost(self, powertrain_type: str) -> float:
        return self.db['infrastructure']['site_preparation'].get(powertrain_type, {}).get('cost_eur', 0.0)
    
    def get_safety_cost(self, powertrain_type: str, n_stations: int = 1) -> float:
        safety = self.db['infrastructure']['safety'].get(powertrain_type, {})
        if 'cost_per_station_eur' in safety:
            return safety['cost_per_station_eur'] * n_stations
        elif 'cost_total_eur' in safety:
            return safety['cost_total_eur']
        return 0.0
    
    def get_licensing_cost(self, powertrain_type: str, country: str) -> float:
        return self.db['infrastructure']['licensing'].get(country, {}).get(powertrain_type, 0.0)
    
    def get_taxes(self, powertrain_type: str, vehicle_weight_class: str, country: str) -> Dict[str, float]:
        try:
            return self.db['taxes'][country][vehicle_weight_class][powertrain_type]
        except KeyError:
            return {'registration': 0.0, 'specific': 0.0}
    
    def get_vehicle_subsidy(self, powertrain_type: str, vehicle_weight_class: str, 
                           purchase_price: float, country: str, year: int) -> float:
        try:
            subsidy_data = self.db['subsidies'][country][str(year)][vehicle_weight_class][powertrain_type]
            if 'vehicle_subsidy_thresholds' in subsidy_data:
                for threshold in subsidy_data['vehicle_subsidy_thresholds']:
                    if purchase_price <= threshold['max_purchase_price']:
                        return threshold['subsidy']
            elif 'vehicle_subsidy' in subsidy_data:
                return subsidy_data['vehicle_subsidy']
        except KeyError:
            pass
        return 0.0
    
    def get_infrastructure_subsidy_rate(self, powertrain_type: str, vehicle_weight_class: str,
                                       country: str, year: int) -> float:
        try:
            subsidy_data = self.db['subsidies'][country][str(year)][vehicle_weight_class][powertrain_type]
            return subsidy_data.get('infrastructure_subsidy_rate', 0.0)
        except KeyError:
            return 0.0
    
    def get_financing_params(self) -> Dict[str, Any]:
        return self.db['financing']


# =============================================================================
# 1. VEHICLE COST SYSTEM
# =============================================================================

class VehicleSystem(System):
    """Calculates vehicle acquisition cost per vehicle"""
    
    def setup(self):
        # Inputs
        self.add_inward('is_new', True, desc='True if buying new vehicle')
        self.add_inward('owns_vehicle', False, desc='True if already owns vehicle')
        self.add_inward('purchase_price', 0.0, desc='Purchase price [EUR]')
        self.add_inward('conversion_cost', 0.0, desc='Conversion cost [EUR]')
        self.add_inward('certification_cost', 0.0, desc='Certification cost [EUR]')
        
        # Output
        self.add_outward('vehicle_cost', 0.0, desc='Vehicle cost per unit [EUR]')
        
    def compute(self):
        if self.is_new:
            self.vehicle_cost = self.purchase_price
        elif self.owns_vehicle:
            self.vehicle_cost = self.conversion_cost + self.certification_cost
        else:
            self.vehicle_cost = self.purchase_price + self.conversion_cost + self.certification_cost


# =============================================================================
# 2. INFRASTRUCTURE COST SYSTEM
# =============================================================================
class FleetSystem(System):
    """Aggregates energy demand from a fleet dictionary to compute total E_total for infrastructure"""

    def setup(self):
        self.add_inward('vehicle_dict', {}, desc='Dictionary of vehicles with energy and shares')

        self.add_outward('E_total_slow', 0.0, desc='Total slow charging energy for the fleet')
        self.add_outward('E_total_fast', 0.0, desc='Total fast charging energy for the fleet')
        self.add_outward('E_total_ultra', 0.0, desc='Total ultra-fast charging energy for the fleet')
        self.add_outward('E_total_private', 0.0, desc='Total private energy for the fleet')

    def compute(self):
        # Générateurs pour chaque type d'énergie
        self.E_total_slow  = sum(E * S for E, S, F, U in 
                                 ((data.get('E_t', 0.0), data.get('S_t', 0.0),
                                   data.get('F_t', 0.0), data.get('U_t', 0.0)) 
                                  for data in self.vehicle_dict.values()))
        
        self.E_total_fast  = sum(E * F for E, S, F, U in 
                                 ((data.get('E_t', 0.0), data.get('S_t', 0.0),
                                   data.get('F_t', 0.0), data.get('U_t', 0.0)) 
                                  for data in self.vehicle_dict.values()))
        
        self.E_total_ultra = sum(E * U for E, S, F, U in 
                                 ((data.get('E_t', 0.0), data.get('S_t', 0.0),
                                   data.get('F_t', 0.0), data.get('U_t', 0.0)) 
                                  for data in self.vehicle_dict.values()))
        self.E_total_private = sum(data.get('Private_t', 0.0) for data in self.vehicle_dict.values())

        
class InfrastructureSystem(System):
    """Calculates infrastructure cost per vehicle"""
    
    def setup(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        object.__setattr__(self, '_db', DatabaseLoader(db_path))
        
        # Inputs
        self.add_inward('powertrain_type', 'bet') # Type de groupe motopropulseur
        self.add_inward('vehicle_number', 1) # Nombre de véhicules dans la flotte
        self.add_inward('E_t', 0.0) # Énergie totale annuelle du véhicule [kWh]
        self.add_inward('S_t', 0.0)     # Part de l'énergie chargée en mode lent
        self.add_inward('F_t', 0.0)    # Part de l'énergie chargée en mode rapide
        self.add_inward('U_t', 0.0)   # Part de l'énergie chargée en mode ultra-rapide
        self.add_inward('Public_t', 0.0)    # Part de l'énergie chargée en mode public
        self.add_inward('n_slow', None)   # Nombre de bornes lentes
        self.add_inward('n_fast', None)     # Nombre de bornes rapides  
        self.add_inward('n_ultra', None)    # Nombre de bornes ultra-rapides
        self.add_inward('E_total_slow', 0.0)    # Énergie totale annuelle en charge lente [kWh]
        self.add_inward('E_total_fast', 0.0)   # Énergie totale annuelle en charge rapide [kWh]
        self.add_inward('E_total_ultra', 0.0)   # Énergie totale annuelle en charge ultra-rapide [kWh]
        self.add_inward('private_t', 0.0)   # Part de l'énergie chargée en mode privé   
        self.add_inward('E_total_private', 0.0)     # Énergie totale annuelle en charge privée [kWh]
        self.add_inward('n_stations', None)     # Nombre de stations
        self.add_inward('smart_charging_enabled', False)    # Smart charging enabled
        self.add_inward('country', 'EU')    # Country for cost parameters
        
        # Outputs
        self.add_outward('infrastructure_cost_per_vehicle', 0.0)  # Infrastructure cost per vehicle [EUR/vehicle]
        self.add_outward('share_slow', 0.0)     # Share of slow charging
        self.add_outward('share_fast', 0.0)     # Share of fast charging
        self.add_outward('share_ultra', 0.0)        # Share of ultra-fast charging
        self.add_outward('n_slow_calculated', 0)        # Calculated number of slow chargers
        self.add_outward('n_fast_calculated', 0)    # Calculated number of fast chargers
        self.add_outward('n_ultra_calculated', 0)       # Calculated number of ultra-fast chargers
        self.add_outward('n_stations_calculated', 0)        # Calculated number of stations
        self.add_outward('hardware_cost', 0.0)  # Hardware cost [EUR/vehicle]
        self.add_outward('software_cost', 0.0)      # Software cost [EUR/vehicle]
        self.add_outward('grid_cost', 0.0)      # Grid connection cost [EUR/vehicle]
        self.add_outward('installation_cost', 0.0)      # Installation cost [EUR/vehicle]
        self.add_outward('site_cost', 0.0)      # Site preparation cost [EUR/vehicle]
        self.add_outward('safety_cost', 0.0)        # Safety cost [EUR/vehicle]
        self.add_outward('licensing_cost', 0.0)     # Licensing cost [EUR/vehicle]
        
    def compute(self):
        slow_params = self._db.get_charger_params('slow')
        fast_params = self._db.get_charger_params('fast')
        ultra_params = self._db.get_charger_params('ultra')

        if self.n_slow is None and self.n_fast is None and self.n_ultra is None:            
            H_demand_slow = self.E_total_slow / (slow_params['power_kw'] * slow_params['charging_efficiency']) if self.E_total_slow > 0 else 0
            H_demand_fast = self.E_total_fast / (fast_params['power_kw'] * fast_params['charging_efficiency']) if self.E_total_fast > 0 else 0
            H_demand_ultra = self.E_total_ultra / (ultra_params['power_kw'] * ultra_params['charging_efficiency']) if self.E_total_ultra > 0 else 0
                
            H_cap_slow = slow_params['operating_hours_per_day'] * slow_params['operating_days_per_year'] 
            H_cap_fast = fast_params['operating_hours_per_day'] * fast_params['operating_days_per_year'] 
            H_cap_ultra = ultra_params['operating_hours_per_day'] * ultra_params['operating_days_per_year'] 
            self.n_slow_calculated = int(np.ceil(H_demand_slow / H_cap_slow)) if H_demand_slow > 0 else 0
            self.n_fast_calculated = int(np.ceil(H_demand_fast / H_cap_fast)) if H_demand_fast > 0 else 0
            self.n_ultra_calculated = int(np.ceil(H_demand_ultra / H_cap_ultra)) if H_demand_ultra > 0 else 0
        else :
            self.n_slow_calculated = self.n_slow
            self.n_fast_calculated = self.n_fast
            self.n_ultra_calculated = self.n_ultra
        self.share_slow = (self.E_t * self.S_t / self.E_total_slow) if self.E_total_slow > 0 else 0
        self.share_fast = (self.E_t * self.F_t / self.E_total_fast) if self.E_total_fast > 0 else 0
        self.share_ultra = (self.E_t * self.U_t / self.E_total_ultra) if self.E_total_ultra > 0 else 0
        self.n_stations_calculated = self.n_stations if self.n_stations is not None else 1

        self.hardware_cost = self._calculate_hardware()
        self.software_cost = self._db.get_software_cost(self.powertrain_type, self.smart_charging_enabled) / max(self.vehicle_number, 1)
        self.grid_cost = self._calculate_grid()
        self.installation_cost = self._calculate_installation()
        self.site_cost = self._db.get_site_cost(self.powertrain_type) / max(self.vehicle_number, 1)
        self.safety_cost = self._db.get_safety_cost(self.powertrain_type, self.n_stations_calculated) / max(self.vehicle_number, 1)
        self.licensing_cost = self._db.get_licensing_cost(self.powertrain_type, self.country) / max(self.vehicle_number, 1)
        self.infrastructure_cost_per_vehicle = (
            self.hardware_cost + self.software_cost + self.grid_cost + 
            self.installation_cost + self.site_cost + self.safety_cost + self.licensing_cost
        )
 
    
    def _calculate_hardware(self) -> float:  
        if self.powertrain_type in ['bet', 'phev']:
            slow_params = self._db.get_charger_params('slow')
            fast_params = self._db.get_charger_params('fast')
            ultra_params = self._db.get_charger_params('ultra')

            return self.n_slow_calculated * self.n_fast_calculated * fast_params['price_eur']*self.share_slow + self.n_fast_calculated * fast_params['price_eur']*self.share_fast + self.n_ultra_calculated * ultra_params['price_eur']*self.share_ultra
        
        else:
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
            
            station_params = self._db.get_station_params(station_type)
            share_private = (self.E_t * self.D_t / self.E_total_private) if self.E_total_private > 0 else 0
            hardware_cost_station = station_params.get('hardware_cost_per_station_eur', 0.0)
            return share_private * self.n_stations * hardware_cost_station
    
    def _calculate_grid(self) -> float:
        if self.powertrain_type in ['bet', 'phev']:
            slow_params = self._db.get_charger_params('slow')
            fast_params = self._db.get_charger_params('fast')
            ultra_params = self._db.get_charger_params('ultra')
            
            total_power = (
                self.n_slow_calculated * slow_params['power_kw'] +
                self.n_fast_calculated * fast_params['power_kw'] +
                self.n_ultra_calculated * ultra_params['power_kw']
            )
            
            grid_cost_total = self._db.get_grid_cost(total_power)
            
            vehicle_power = (
                self.n_slow_calculated * slow_params['power_kw'] * self.share_slow +
                self.n_fast_calculated * fast_params['power_kw'] * self.share_fast +
                self.n_ultra_calculated * ultra_params['power_kw'] * self.share_ultra
            )
            contribution = vehicle_power / total_power if total_power > 0 else 0
            return grid_cost_total * contribution
        elif self.powertrain_type in ['fcet', 'hice']:
            h2_params = self._db.get_station_params('h2')
            return self.n_stations_calculated * h2_params.get('electrolyzer_grid_connection_cost_eur', 0.0) / max(self.vehicle_number, 1)
        elif self.powertrain_type in ['gnv', 'lng']:
            station_params = self._db.get_station_params(self.powertrain_type)
            return self.n_stations_calculated * station_params.get('electricity_connection_cost_eur', 0.0) / max(self.vehicle_number, 1)
        return 0.0
    
    def _calculate_installation(self) -> float:
        if self.powertrain_type in ['bet', 'phev']:
            slow_params = self._db.get_charger_params('slow')
            fast_params = self._db.get_charger_params('fast')
            ultra_params = self._db.get_charger_params('ultra')
            
            return (
                self.n_slow_calculated * slow_params['installation_cost_eur'] * self.share_slow +
                self.n_fast_calculated * fast_params['installation_cost_eur'] * self.share_fast +
                self.n_ultra_calculated * ultra_params['installation_cost_eur'] * self.share_ultra
            )
        elif self.powertrain_type in ['fcet', 'hice']:
            h2_params = self._db.get_station_params('h2')
            return self. n_stations_calculated * h2_params.get('installation_cost_per_station_eur', 0.0) / max(self.vehicle_number, 1)
        elif self.powertrain_type in ['gnv', 'lng']:
            station_params = self._db.get_station_params(self.powertrain_type)
            return self.n_stations_calculated * station_params.get('installation_cost_per_station_eur', 0.0) / max(self.vehicle_number, 1)
        else:
            diesel_params = self._db.get_station_params('diesel')
            return self.n_stations_calculated * diesel_params.get('installation_cost_per_pump_eur', 0.0) / max(self.vehicle_number, 1)


# =============================================================================
# 3. TAXES SYSTEM
# =============================================================================

class TaxesSystem(System):
    """Calculates taxes"""
    
    def setup(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        object.__setattr__(self, '_db', DatabaseLoader(db_path))
        
        self.add_inward('powertrain_type', 'bet')
        self.add_inward('vehicle_weight_class', 'heavy')
        self.add_inward('country', 'EU')
        self.add_outward('registration_tax', 0.0)

        
    def compute(self):
        taxes = self._db.get_taxes(self.powertrain_type, self.vehicle_weight_class, self.country)
        self.registration_tax = taxes.get('registration', 0.0)
   


# =============================================================================
# 4. SUBSIDIES SYSTEM
# =============================================================================

class SubsidiesSystem(System):
    """Calculates subsidies"""
    
    def setup(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        object.__setattr__(self, '_db', DatabaseLoader(db_path))
        
        self.add_inward('powertrain_type', 'bet')
        self.add_inward('vehicle_weight_class', 'heavy')
        self.add_inward('vehicle_cost_per_unit', 0.0)
        self.add_inward('infrastructure_cost_per_vehicle', 0.0)
        self.add_inward('country', 'EU')
        self.add_inward('year', 2025)
        self.add_inward('vehicle_number', 1)
        
        self.add_outward('vehicle_subsidy', 0.0)
        self.add_outward('infrastructure_subsidy', 0.0)
        self.add_outward('total_subsidies', 0.0)
        
    def compute(self):
        self.vehicle_subsidy = self._db.get_vehicle_subsidy(
            self.powertrain_type, self.vehicle_weight_class,
            self.vehicle_cost_per_unit, self.country, self.year
        )        

        infra_rate = self._db.get_infrastructure_subsidy_rate(
            self.powertrain_type, self.vehicle_weight_class, self.country, self.year
        )
        self.infrastructure_subsidy = self.infrastructure_cost_per_vehicle * infra_rate
        self.total_subsidies = self.vehicle_subsidy + self.infrastructure_subsidy / max(self.vehicle_number, 1)


# =============================================================================
# 5. FINANCING SYSTEM
# =============================================================================

class FinancingSystem(System):
    """Calculates financing cost"""
    
    def setup(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        object.__setattr__(self, '_db', DatabaseLoader(db_path))
        
        self.add_inward('total_vehicle_cost', 0.0)
        self.add_inward('powertrain_type', 'bet')
        self.add_inward('loan_years', 10)
        
        self.add_outward('base_interest_rate', 0.0)
        self.add_outward('esg_adjustment_rate', 0.0)
        self.add_outward('adjusted_interest_rate', 0.0)
        self.add_outward('origination_cost', 0.0)
        self.add_outward('total_financing_cost', 0.0)
        self.add_outward('crf', 1.0)
        
    def compute(self):
        fin_params = self._db.get_financing_params()
        
        self.base_interest_rate = fin_params['base_interest_rate']
        self.esg_adjustment_rate = fin_params['esg_adjustments'].get(self.powertrain_type, 0.0)
        self.adjusted_interest_rate = self.base_interest_rate + self.esg_adjustment_rate
        
        origination_rate = fin_params['origination_fee_rate']
        self.origination_cost = self.total_vehicle_cost * origination_rate
        self.total_financing_cost = self.origination_cost 
        r = self.adjusted_interest_rate
        n = self.loan_years
        self.crf = (r * (1+r)**n) / ((1+r)**n - 1) if r > 0 else 1.0  # si r=0, CRF=1

# =============================================================================
# 6. CAPEX SYSTEM (AGGREGATES ALL)
# =============================================================================

class CAPEXSystem(System):
    """Complete CAPEX system aggregating all components with FleetSystem"""
    
    def setup(self, db_path: str = r"c:\Users\pc\Downloads\database.json"):
        object.__setattr__(self, '_db', DatabaseLoader(db_path))
        
        # --- Add subsystems ---
        self.add_child(VehicleSystem('vehicle'))
        self.add_child(FleetSystem('fleet'))  # Système de flotte
        self.add_child(InfrastructureSystem('infrastructure', db_path=db_path))
        self.add_child(TaxesSystem('taxes', db_path=db_path))
        self.add_child(SubsidiesSystem('subsidies', db_path=db_path))
        self.add_child(FinancingSystem('financing', db_path=db_path))
        
        # --- USER INPUTS ---
        self.add_inward('powertrain_type', 'bet')
        self.add_inward('vehicle_number', 1)
        self.add_inward('id', 1)    
        self.add_inward('vehicle_weight_class', 'heavy')
        self.add_inward('country', 'EU')
        self.add_inward('year', 2025)
        self.add_inward('n_slow', None)
        self.add_inward('n_fast', None)
        self.add_inward('n_ultra', None)
        
        # Vehicle
        self.add_inward('is_new', True)
        self.add_inward('owns_vehicle', False)
        self.add_inward('purchase_price', 0.0)
        self.add_inward('conversion_cost', 0.0)
        self.add_inward('certification_cost', 0.0)
        
        # Energy
        self.add_inward('E_t', 0.0)
        self.add_inward('S_t', 0.0)
        self.add_inward('F_t', 0.0)
        self.add_inward('U_t', 0.0)
        self.add_inward('Public_t', 0.0)
        self.add_inward('private_t', 0.0)
        self.add_inward('E_total_private', 0.0)
        self.add_inward('n_stations', None)
        self.add_inward('smart_charging_enabled', False)
        
        # --- VEHICLE DICTIONARY (Fleet) ---
        self.add_inward('vehicle_dict', {})  # clé=id, valeur=VehicleSystem
        
        # --- OUTPUTS ---
        self.add_outward('total_capex', 0.0)
        self.add_outward('capex_per_vehicle', 0.0)
        self.add_outward('vehicle_cost_component', 0.0)
        self.add_outward('infrastructure_cost_component', 0.0)
        self.add_outward('taxes_component', 0.0)
        self.add_outward('financing_component', 0.0)
        self.add_outward('subsidies_component', 0.0)
        self.add_outward('crf', 1.0)
    
    def compute(self):
        # --- 1. Vehicle ---
        self.vehicle.is_new = self.is_new
        self.vehicle.owns_vehicle = self.owns_vehicle
        self.vehicle.purchase_price = self.purchase_price
        self.vehicle.conversion_cost = self.conversion_cost
        self.vehicle.certification_cost = self.certification_cost
        self.vehicle.run_once()
        self.vehicle_cost_component = self.vehicle.vehicle_cost
        
        # --- 2. Fleet (calcul des énergies totales) ---
        self.fleet.vehicle_dict = self.vehicle_dict  # Dictionnaire de véhicules
        self.fleet.run_once()
        
        # --- 3. Infrastructure ---
        self.infrastructure.powertrain_type = self.powertrain_type
        self.infrastructure.vehicle_number = len(self.vehicle_dict)  # Nombre de véhicules dans le dictionnaire
        if self.powertrain_type in ['bet', 'phev']:
            self.infrastructure.E_t = self.vehicle_dict[self.id]["E_t"]
            self.infrastructure.S_t = self.vehicle_dict[self.id]["S_t"]
            self.infrastructure.F_t = self.vehicle_dict[self.id]["F_t"]
            self.infrastructure.U_t = self.vehicle_dict[self.id]["U_t"]
            self.infrastructure.Public_t = self.vehicle_dict[self.id]["Public_t"]
        else:
            self.infrastructure.Private_t = self.vehicle_dict[self.id]["private_t"]
        self.infrastructure.E_total_slow = self.fleet.E_total_slow
        self.infrastructure.E_total_fast = self.fleet.E_total_fast
        self.infrastructure.E_total_ultra = self.fleet.E_total_ultra
        self.infrastructure.E_total_private = self.E_total_private
        self.infrastructure.n_stations = self.n_stations
        self.infrastructure.n_slow = self.n_slow
        self.infrastructure.n_fast = self.n_fast
        self.infrastructure.n_ultra = self.n_ultra  
        self.infrastructure.smart_charging_enabled = self.smart_charging_enabled
        self.infrastructure.country = self.country
        self.infrastructure.run_once()
        self.infrastructure_cost_component = self.infrastructure.infrastructure_cost_per_vehicle
        
        # --- 4. Taxes ---
        self.taxes.powertrain_type = self.powertrain_type
        self.taxes.vehicle_weight_class = self.vehicle_weight_class
        self.taxes.country = self.country
        self.taxes.run_once()
        self.taxes_component = self.taxes.registration_tax
        
        # --- 5. Subsidies ---
        self.subsidies.powertrain_type = self.powertrain_type
        self.subsidies.vehicle_weight_class = self.vehicle_weight_class
        self.subsidies.vehicle_cost_per_unit = self.vehicle.vehicle_cost
        self.subsidies.infrastructure_cost_per_vehicle = self.infrastructure.infrastructure_cost_per_vehicle
        self.subsidies.country = self.country
        self.subsidies.year = self.year
        self.subsidies.vehicle_number = self.vehicle_number
        self.subsidies.run_once()
        self.subsidies_component = self.subsidies.total_subsidies
        
        # --- 6. Financing ---
        self.financing.total_vehicle_cost = self.vehicle_cost_component
        self.financing.powertrain_type = self.powertrain_type
        self.financing.run_once()
        self.financing_component = self.financing.total_financing_cost
        self.crf = self.financing.crf
        
        # --- TOTAL CAPEX ---
        self.total_capex = (
            self.vehicle_cost_component +
            self.infrastructure_cost_component +
            self.taxes_component +
            self.financing_component -
            self.subsidies_component
        )
        self.capex_per_vehicle = self.total_capex * self.crf
        
    def print_results(self):
        print("\n" + "="*80)
        print("CAPEX CALCULATION RESULTS")
        print("="*80)
        print(f"Powertrain: {self.powertrain_type}")
        print(f"Vehicle Number: {self.vehicle_number}")
        print(f"Country: {self.country}")
        print("-"*80)
        print(f"Vehicle Cost: €{self.vehicle_cost_component:,.2f}")
        print(f"Infrastructure Cost: €{self.infrastructure_cost_component:,.2f}")
        print(f"Taxes: €{self.taxes_component:,.2f}")
        print(f"Financing: €{self.financing_component:,.2f}")
        print(f"Subsidies: -€{self.subsidies_component:,.2f}")
        print("-"*80)
        print(f"Total CAPEX: €{self.total_capex:,.2f}")
        print(f"CAPEX per Vehicle: €{self.capex_per_vehicle:,.2f}")


if __name__ == "__main__":
    from cosapp.drivers import RunOnce
    
    print("CAPEX Calculator - Database-Driven System\n")
    
    # Example 1: BET
    print("### Example 1: Battery Electric Truck (BET) ###")
    sys1 = CAPEXSystem('capex_bet')
    sys1.powertrain_type = 'bet'
    sys1.id = 1    
    sys1.vehicle_weight_class = 'heavy' 
    sys1.country = 'EU'
    sys1.year = 2025    
    sys1.is_new = True
    sys1.owns_vehicle = False
    sys1.purchase_price = 80000.0
    sys1.conversion_cost = 0.0
    sys1.certification_cost = 0.0
    sys1.vehicle_dict = {
        1: {'E_t': 15000.0, 'S_t': 0.3, 'F_t': 0.4, 'U_t': 0.1,'Public_t': 0.2},
        2: {'E_t': 12000.0, 'S_t': 0.6, 'F_t': 0.3, 'U_t': 0.1,'Public_t': 0.0},
    }

    
    driver1 = sys1.add_driver(RunOnce('run1'))
    sys1.run_drivers()
    sys1.print_results()