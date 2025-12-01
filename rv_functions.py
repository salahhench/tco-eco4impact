# %%
"""
Residual Value (RV) Calculator - CoSApp Implementation
"""

from cosapp.base import System, Port
import json
import math
from datetime import datetime

# %%
class VehiclePropertiesPort(Port):
    '''
    Port for Vehicle Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        # -------------------- USER INPUTS --------------------
        self.add_variable('type_vehicle', dtype=str, desc='Vehicle type: Truck or Ship', value='truck')
        self.add_variable('type_energy', dtype=str, desc='Energy type: diesel, electric, hybrid, hydrogen_fuel_cell, hydrogen_h2, cng, lng', value='diesel')
        self.add_variable('registration_country', dtype=str, desc='Registration country of the vehicle', value='France')
        
        self.add_variable('purchase_cost', dtype=float, desc='Initial purchase cost', value=0.0)
        self.add_variable('travel_measure', dtype=float, desc='Total Distance (km) or hours (h)', value=0.0)
        self.add_variable('maintenance_cost', dtype=float, desc='Total maintenance cost incurred', value=0.0)
        
        self.add_variable('minimum_fuel_consumption', dtype=float, desc='SFC (g/kWh)', value=250.0)
        self.add_variable('consumption_real', dtype=float, desc='Real consumption (kWh/km or kg/100km)', value=0.0)
        self.add_variable('utility_factor', dtype=float, desc='Electric fraction for hybrids', value=0.0)
        
        self.add_variable('E_annual_kwh', dtype=float, desc='Annual energy consumption (kWh)', value=0.0)
        self.add_variable('C_bat_kwh', dtype=float, desc='Battery capacity (kWh)', value=0.0)
        self.add_variable('DoD', dtype=float, desc='Depth of discharge', value=0.8)
        self.add_variable('S_slow', dtype=float, desc='Proportion slow charging', value=0.0)
        self.add_variable('S_fast', dtype=float, desc='Proportion fast charging', value=0.0)
        self.add_variable('S_ultra', dtype=float, desc='Proportion ultra-fast charging', value=0.0)
        
        self.add_variable('powertrain_model_year', dtype=int, desc='Powertrain model year', value=2020)
        
        self.add_variable('warranty', dtype=float, desc='Warranty duration (years or km)', value=5.0)
        self.add_variable('type_warranty', dtype=str, desc='Type of warranty: years or km', value='years')
        self.add_variable('year_purchase', dtype=int, desc='Year of purchase', value=2020)
        
        self.add_variable('current_year', dtype=int, desc='Current year', value=datetime.now().year)


class CountryPropertiesPort(Port):
    '''
    Port for Country Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        self.add_variable('energy_price', dtype=float, desc='Energy price ($/L)', value=0.0)
        self.add_variable('c02_taxes', dtype=float, desc='CO2 taxes ($)', value=0.0)
        self.add_variable('subsidies', dtype=float, desc='Subsidies ($)', value=0.0)


class ResidualValueCalculator(System):
    '''
    Residual Value (RV) Calculator System
    
    OPEX Components:
    - DEPRECIATION
    - IMPACT HEALTH: 
        - EFICIENCY
        - CHARGING
        - OBSOLESCENCE
        - WARRANTY
    - EXTERNAL FACTORS
    '''
    def setup(self, type_vehicle: str = "truck"):
        
        db_path = f"db_rv_{type_vehicle}.json"
        
        # Load database
        with open(db_path, 'r') as f:
            db_rv = json.load(f)

        object.__setattr__(self, '_countries_data',
                           {c['country']: c['data_country'] for c in db_rv['countries']})
        
        object.__setattr__(self, '_vehicles_data',db_rv['vehicle'])
        
        # # Add ports # SHOULD WE OMITE THIS PART?
        self.add_input(VehiclePropertiesPort, 'in_vehicle_properties')
        self.add_input(CountryPropertiesPort, 'in_country_properties')


        # Add output variables
        self.add_outward('total_depreciation', 0.0, desc='Total depreciation cost')
        self.add_outward('efficiency_penalty', 0.0, desc='Efficiency penalty (%)')
        self.add_outward('obsolescence_penalty', 0.0, desc='Obsolescence penalty (%)')
        self.add_outward('charging_penalty', 0.0, desc='Charging penalty (%)')
        self.add_outward('warranty_penalty', 0.0, desc='Warranty penalty (%)')
        self.add_outward('total_impact_health', 0.0, desc='Total impact health penalty')
        self.add_outward('total_external_factors', 0.0, desc='Total external factors adjustment')
        self.add_outward('rv', 0.0, desc='Final Residual Value')


    # COMPUTE METHODS FOR RV CALCULATION

    # 1.- DEPRECIATION
    def compute_depreciation(self):
        '''
        Formula:        
        :param self: Description
        '''
        # Inputs
        vp = self.in_vehicle_properties
        type_vehicle = vp.type_vehicle
        type_energy = vp.type_energy
        country = vp.registration_country

        # Parameters of database
        rate_per_year = self._countries_data[country]["depreciation"]["depreciation_rate_per_year"][type_energy]
        rate_by_usage = self._countries_data[country]["depreciation"]["depreciation_rate_by_usage"][type_energy]
        coef_maintenance = self._countries_data[country]["depreciation"]["coef_depreciation_maintenance"][type_energy]

        # Depreciation components
        purchase_cost = vp.purchase_cost
        vehicle_age = vp.current_year - vp.year_purchase
        dep_per_year = rate_per_year * vehicle_age
        dep_by_usage = rate_by_usage * vp.travel_measure
        dep_maintenance = coef_maintenance * vp.maintenance_cost

        # Total depreciation
        self.total_depreciation = purchase_cost - (dep_per_year + dep_by_usage + dep_maintenance)

    # 2.1.- PENALIZATION OF EFICIENCY
    def compute_eficiency(self):
        # Inputs
        vp = self.in_vehicle_properties
        type_vehicle = vp.type_vehicle
        type_energy = vp.type_energy
        

        # Depends of the type of energy:
        if type_energy in ["diesel", "hydrogen_h2", "cng", "lng"]:
            minimum_fuel_consumption = vp.minimum_fuel_consumption
            heating_value = self._vehicles_data["heating_value"][type_energy]
            # ICE vehicles: η_f = 3600 / (SFC * Q_HV)
            n_f = 3600/(minimum_fuel_consumption * heating_value)
        
        elif type_energy in ["electric", "hydrogen_fuel_cell"]:
            # Electric/Fuel Cell: η_sys = consumption_benchmark / consumption_real
            consumption_real = vp.consumption_real
            consumption_benchmark = self._vehicles_data["consumption_benchmark"][type_energy]

            if consumption_real>0:
                n_f = consumption_benchmark / consumption_real
            else:
                n_f = 0.85
        
        elif type_energy in ["HEV", "PHEV"]:
            # Hybrid: η_hybrid = 1 / [(α/η_EV) + (1-α)/η_ICE]
            utility_factor = vp.utility_factor
            n_ev = self._vehicles_data["n_ev"][type_energy]
            n_ice = self._vehicles_data["n_ice"][type_energy]

            if utility_factor>0 and utility_factor <1:
                n_f = 1.0/((utility_factor/n_ev)+((1-utility_factor)/n_ice))
            else:
                n_f = n_ice
        else:
            n_f = 0.40 # Default
        
        self.efficiency_penalty = (1.0 - n_f)*100.0
        
    # 2.2.- OBSOLESCENCE
    def compute_obsolescence(self):
        # Inputs
        vp = self.in_vehicle_properties
        type_vehicle = vp.type_vehicle
        type_energy = vp.type_energy
        country = vp.registration_country
        powertrain_model_year = vp.powertrain_model_year

        # Parameters of database
        yearly_obsolescence_rate = self._countries_data[country]["yearly_obsolescence_rate"][type_energy]

        # Output
        DM = math.exp(-yearly_obsolescence_rate * (vp.current_year - powertrain_model_year) )
        
        self.obsolescence_penalty = (1.0-DM)*100

    # 2.3.- CHARGING
    def compute_charging(self):
        # Inputs
        vp = self.in_vehicle_properties
        type_vehicle = vp.type_vehicle
        type_energy = vp.type_energy

        if type_energy == "electric":
            E_annual_kwh = vp.E_annual_kwh
            C_bat_kwh = vp.C_bat_kwh
            DoD = vp.DoD
            S_slow = vp.S_slow
            S_fast = vp.S_fast
            S_ultra = vp.S_ultra

            # Parameters of database
            d_slow = self._vehicles_data["d_slow"][type_energy]
            d_fast = self._vehicles_data["d_fast"][type_energy]
            d_ultra = self._vehicles_data["d_ultra"][type_energy]
            k_d = self._vehicles_data["k_d"][type_energy]
        
            # Average degradation per cycle
            degradation_per_cycle = (S_slow * d_slow + 
                                   S_fast * d_fast + 
                                   S_ultra * d_ultra)
            
            # Equivalent full cycles per year
            if C_bat_kwh > 0 and DoD > 0:
                cycles = E_annual_kwh / (C_bat_kwh * DoD)
            else:
                cycles = 0.0
            
            # Total annual degradation
            D = cycles * degradation_per_cycle
            
            # Charging health factor (exponential decay)
            health_charging = math.exp(-k_d * D)
            
            # Penalization: charging = 1 - health_charging
            self.charging_penalty = (1.0 - health_charging) * 100.0
        else:
            self.charging_penalty = 0.0

    # 2.4.- COMPUTE WARRANTY
    def compute_warranty(self):
        # Inputs
        vp = self.in_vehicle_properties
        warranty = vp.warranty
        type_warranty = vp.type_warranty
        year_purchase = vp.year_purchase
        DW = 0.0

        if type_warranty=="year":
            elapsed = vp.current_year - year_purchase

            if warranty>0:
                DW = 1.0 - (elapsed/warranty)
            else:
                DW= 0.0
        elif type_warranty=="km":
            elapsed = vp.travel_measure

            if warranty>0:
                DW = 1.0 - (elapsed/warranty)
            else:
                DW = 0.0
        else:
            print("Obs.: type_warranty only can be year or km")

        # Penalization
        self.warranty_penalty = (1.0-DW)*100


    # 2.- IMPACT HEALTH
    def compute_impact_health(self):
        self.compute_eficiency()
        self.compute_obsolescence()
        self.compute_charging()
        self.compute_warranty()

        # Compute IMPACT HEALTH
        self.total_impact_health = (self.efficiency_penalty+self.obsolescence_penalty+self.charging_penalty+self.warranty_penalty)
    
    # 3.- EXTERNAL FACTORS
    def compute_external_factors(self):
        # Inputs
        cp = self.in_country_properties
        vp = self.in_vehicle_properties
        energy_price = cp.energy_price
        c02_taxes = cp.c02_taxes
        subsidies = cp.subsidies
        type_vehicle = vp.type_vehicle
        type_energy = vp.type_energy
        country = vp.registration_country


        # Parameters of database
        energy_price_factor = self._countries_data[country]["external_factors"]["energy_price_factor"][type_energy]
        cO2_taxes_factor = self._countries_data[country]["external_factors"]["CO2_taxes_factor"]
        subsidies_factor = self._countries_data[country]["external_factors"]["subsidies_factor"][type_energy]

        # Total external_factors
        self.total_external_factors = energy_price_factor*energy_price+ c02_taxes*cO2_taxes_factor + subsidies*subsidies_factor

    # 4.- RV
    def compute(self):
        self.compute_depreciation()
        self.compute_impact_health()
        self.compute_external_factors()

        self.rv = (self.total_depreciation+self.total_impact_health+self.total_external_factors)
