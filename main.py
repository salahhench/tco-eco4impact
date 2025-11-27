"""
Residual Value (RV) Calculator - CoSApp Implementation
"""

from cosapp.base import System, Port
import json
import math
from datetime import datetime

# %%
# class RVPort(Port):
#     '''
#     Port for RV Calculation inputs and outputs for ships and trucks.
#     '''

#     def setup(self):
#         # -------------------- USER INPUTS (ORANGE) --------------------
#         self.add_variable('type_vehicle', dtype = str, desc = 'Vehicle type: Truck or Ship')
#         self.add_variable('type_energy', dtype = str, desc = 'Energy type: Diesel_fosile, Diesel_hibrid, BET, Fuel_cell, etc')
#         self.add_variable('registration_country', dtype = str, desc = 'Registration country of the vehicle')

#         self.add_variable('current_year', dtype = int, desc = 'Current year') # Obs. You can get it from datetime.now().year



#         # SUB-MODULE 1: Depreciation Calculation
#         self.add_variable('purchase_cost', dtype = float, desc = 'Initial purchase cost')
#         self.add_variable('age_vehicle', dtype = float, desc = 'Age of vehicle (years)')
#         self.add_variable('travel_measure', dtype = float, desc = 'Distance (km) or hours (h)')
#         self.add_variable('maintenance_cost', dtype = float, desc = 'Total maintenance cost incurred')

        
#         # SUB-MODULE 2: IMPACT HEALTH
#         # 1.- TECH
#         self.add_variable('minimum_fuel_consumption', dtype = float, desc = 'SFC (g/kWh)')
#         self.add_variable('consumption_real', dtype = float, desc = 'Real consumption (kWh/km or kg/100km)')
#         self.add_variable('utility_factor', dtype = float, desc = 'Electric fraction for hybrids')

#         # 2.- CHARGING
#         self.add_variable('E_annual_kwh', dtype = float, desc = 'Annual energy consumption (kWh)')
#         self.add_variable('C_bat_kwh', dtype = float, desc = 'Battery capacity (kWh)')
#         self.add_variable('DoD', dtype = float, desc = 'Depth of discharge')
#         self.add_variable('S_slow', dtype = float, desc = 'Proportion slow charging')
#         self.add_variable('S_fast', dtype = float, desc = 'Proportion fast charging')
#         self.add_variable('S_ultra', dtype = float, desc = 'Proportion ultra-fast charging')

#         # 3.- OBSOLESCENCE
#         self.add_variable('powertrain_model_year', dtype = int, desc = 'Powertrain model year')

#         # 4.- WARRANTY
#         self.add_variable('warranty', dtype = float, desc = 'Warranty duration (years or km)')
#         self.add_variable('type_warranty', dtype = str, desc = 'Type of warranty: years or km')
#         self.add_variable('year_purchase', dtype = int, desc = 'Year of purchase')

#         # 5.- QUALITY
#         # It's variables are only type_energy and type_vehicle defined above

#         # SUB-MODULE 3: EXTERNAL FACTORS
#         self.add_variable('energy_price', dtype = float, desc = 'Energy price ($/L)')
#         self.add_variable('c02_taxes', dtype = float, desc = 'CO2 taxes ($)')
#         self.add_variable('subsidies', dtype = float, desc = 'Subsidies ($)')

# %%
class VehicleProperties(Port):
    '''
    Port for Vehicle Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        # -------------------- USER INPUTS --------------------
        self.add_variable('type_vehicle', dtype = str, desc = 'Vehicle type: Truck or Ship')
        self.add_variable('type_energy', dtype = str, desc = 'Energy type: Diesel_fosile, Diesel_hibrid, BET, Fuel_cell, etc')
        self.add_variable('registration_country', dtype = str, desc = 'Registration country of the vehicle')
        
        self.add_variable('purchase_cost', dtype = float, desc = 'Initial purchase cost')
        # self.add_variable('age_vehicle', dtype = float, desc = 'Age of vehicle (years) -> Current year - year of purchase (because if it is used vehicle, the year of purchase is not the model year, and we have to consider the depreciation that we have made since we bought it)')
        self.add_variable('travel_measure', dtype = float, desc = 'Total Distance (km) or hours (h) -> Total distance or hours travelled by the vehicle until now')
        self.add_variable('maintenance_cost', dtype = float, desc = 'Total maintenance cost incurred -> Total maintenance cost incurred until now')
        
        self.add_variable('minimum_fuel_consumption', dtype = float, desc = 'SFC (g/kWh)')
        self.add_variable('consumption_real', dtype = float, desc = 'Real consumption (kWh/km or kg/100km) -> Real consumption of the vehicle, can be obtained from telematics data')
        self.add_variable('utility_factor', dtype = float, desc = 'Electric fraction for hybrids -> For hybrid vehicles, the fraction of distance travelled in electric mode')
        
        self.add_variable('E_annual_kwh', dtype = float, desc = 'Annual energy consumption (kWh) -> Annual energy consumption of the vehicle in kWh')
        self.add_variable('C_bat_kwh', dtype = float, desc = 'Battery capacity (kWh)')
        self.add_variable('DoD', dtype = float, desc = 'Depth of discharge')
        self.add_variable('S_slow', dtype = float, desc = 'Proportion slow charging')
        self.add_variable('S_fast', dtype = float, desc = 'Proportion fast charging')
        self.add_variable('S_ultra', dtype = float, desc = 'Proportion ultra-fast charging')
        
        self.add_variable('powertrain_model_year', dtype = int, desc = 'Powertrain model year')
        
        self.add_variable('warranty', dtype = float, desc = 'Warranty duration (years or km)')
        self.add_variable('type_warranty', dtype = str, desc = 'Type of warranty: years or km')
        self.add_variable('year_purchase', dtype = int, desc = 'Year of purchase') # To calculate the age of the vehicle
        
        self.add_variable('current_year', dtype = int, desc = 'Current year') # Obs. You can get it from datetime.now().year
        # self.add_variable('current_year', datetime.now().year, desc='Current year')


class CountryProperties(Port):
    '''
    Port for Country Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        self.add_variable('energy_price', dtype = float, desc = 'Energy price ($/L)')
        self.add_variable('c02_taxes', dtype = float, desc = 'CO2 taxes ($)')
        self.add_variable('subsidies', dtype = float, desc = 'Subsidies ($)')


class ResidualValueCalculator(System):
    '''
    Residual Value (RV) Calculator System
    
    OPEX Components:
    - DEPRECIATION
    - IMPACT HEALTH: 
        - TECH
        - CHARGING
        - OBSOLESCENCE
        - WARRANTY
        - QUALITY
    - EXTERNAL FACTORS
    '''
    def setup(self, db_path='database_rv.json'):
        # Load database
        with open(db_path, 'r') as f:
            db_rv = json.load(f)

        object.__setattr__(self, '_countries_data',
                           {c['country']: c['data_country'] for c in db_rv['countries']})
        
        object.__setattr__(self, '_vehicles_data',db_rv['vehicle'])
        
        # Add ports
        self.add_inward('in_vehicle_properties', VehicleProperties, desc='Vehicle Properties')
        self.add_inward('in_country_properties', CountryProperties, desc='Country Properties')


    # COMPUTE METHODS FOR RV CALCULATION

    # 1.- DEPRECIATION
    def compute_depreciation(self):
        '''
        Formula:        
        :param self: Description
        '''

        # Inputs
        type_vehicle = self.in_vehicle_properties.type_vehicle
        type_energy = self.in_vehicle_properties.type_energy
        country = self.in_vehicle_properties.registration_country

        # Parameters of database
        rate_per_year = self._countries_data[country]["depreciation"]["depreciation_rate_per_year"][type_vehicle][type_energy]
        rate_by_usage = self._countries_data[country]["depreciation"]["depreciation_rate_by_usage"][type_vehicle][type_energy]
        coef_maintenance = self._countries_data[country]["depreciation"]["coef_depreciation_maintenance"][type_vehicle][type_energy]

        # Depreciation components
        purchase_cost = self.in_vehicle_properties.purchase_cost
        vehicle_age = self.in_vehicle_properties.current_year - self.in_vehicle_properties.year_purchase
        dep_per_year = rate_per_year * vehicle_age
        dep_by_usage = rate_by_usage * self.in_vehicle_properties.travel_measure
        dep_maintenance = coef_maintenance * self.in_vehicle_properties.maintenance_cost

        # Total depreciation
        self.total_depreciation = purchase_cost - (dep_per_year + dep_by_usage + dep_maintenance)

    # 2.1.- PENALIZATION OF EFICIENCY
    def compute_eficiency(self):
        # Inputs
        type_vehicle = self.in_vehicle_properties.type_vehicle
        type_energy = self.in_vehicle_properties.type_energy
        minimum_fuel_consumption = self.in_vehicle_properties.minimum_fuel_consumption
        consumption_real = self.in_vehicle_properties.consumption_real
        utility_factor = self.in_vehicle_properties.utility_factor

        # Parameters of database
        consumption_benchmark = self._vehicles_data["consumption_benchmark"][type_vehicle][type_energy]
        heating_value = self._vehicles_data["heating_value"][type_vehicle][type_energy]
        n_ev = self._vehicles_data["n_ev"][type_vehicle][type_energy]
        n_ice = self._vehicles_data["n_ice"][type_vehicle][type_energy]


        # Depends of the type of energy:
        if type_energy in ["diesel", "hydrogen_h2", "cng", "lng"]:
            # ICE vehicles: η_f = 3600 / (SFC * Q_HV)
            n_f = 3600/(minimum_fuel_consumption * heating_value)
        
        elif type_energy in ["electric", "hydrogen_fuel_cell"]:
            # Electric/Fuel Cell: η_sys = consumption_benchmark / consumption_real
            if consumption_real>0:
                n_f = consumption_benchmark / consumption_real
            else:
                n_f = 0.85
        
        elif type_energy in ["HEV", "PHEV"]:
            # Hybrid: η_hybrid = 1 / [(α/η_EV) + (1-α)/η_ICE]
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
        type_vehicle = self.in_vehicle_properties.type_vehicle
        type_energy = self.in_vehicle_properties.type_energy
        country = self.in_vehicle_properties.registration_country
        powertrain_model_year = self.in_vehicle_properties.powertrain_model_year

        # Parameters of database
        yearly_obsolescence_rate = self._countries_data[country]["yearly_obsolescence_rate"][type_vehicle][type_energy]

        # Output
        DM = math.exp(-yearly_obsolescence_rate * (self.in_vehicle_properties.current_year - powertrain_model_year) )
        
        self.obsolescence_penalty = (1.0-DM)*100

    # 2.3.- CHARGING
    def compute_charging(self):
        # Inputs
        type_vehicle = self.in_vehicle_properties.type_vehicle
        type_energy = self.in_vehicle_properties.type_energy

        E_annual_kwh = self.in_vehicle_properties.E_annual_kwh
        C_bat_kwh = self.in_vehicle_properties.C_bat_kwh
        DoD = self.in_vehicle_properties.DoD
        S_slow = self.in_vehicle_properties.S_slow
        S_fast = self.in_vehicle_properties.S_fast
        S_ultra = self.in_vehicle_properties.S_ultra

        # Parameters of database
        d_slow = self._vehicles_data["d_slow"][type_vehicle][type_energy]
        d_fast = self._vehicles_data["d_fast"][type_vehicle][type_energy]
        d_ultra = self._vehicles_data["d_ultra"][type_vehicle][type_energy]
        k_d = self._vehicles_data["k_d"][type_vehicle][type_energy]

        if self.type_energy == "electric":
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

    # 2.4.- COMPUTE WARRANTY
    def compute_warranty(self):
        # Inputs
        warranty = self.in_vehicle_properties.warranty
        type_warranty = self.in_vehicle_properties.type_warranty
        year_purchase = self.in_vehicle_properties.year_purchase

        if type_warranty=="year":
            elapsed = self.in_vehicle_properties.current_year - year_purchase

            if warranty>0:
                DW = 1.0 - (elapsed/warranty)
            else:
                DW= 0.0
        elif type_warranty=="km":
            elapsed = self.in_vehicle_properties.travel_measure

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
        energy_price = self.in_country_properties.energy_price
        c02_taxes = self.in_country_properties.c02_taxes
        subsidies = self.in_country_properties.subsidies
        type_vehicle = self.in_vehicle_properties.type_vehicle
        type_energy = self.in_vehicle_properties.type_energy
        country = self.in_vehicle_properties.registration_country


        # Parameters of database
        energy_price_factor = self._countries_data[country]["external_factors"]["energy_price_factor"][type_vehicle][type_energy]
        cO2_taxes_factor = self._countries_data[country]["external_factors"]["CO2_taxes_factor"]
        subsidies_factor = self._countries_data[country]["external_factors"]["subsidies_factor"][type_vehicle][type_energy]

        # Total external_factors
        self.total_external_factors = energy_price_factor*energy_price+ c02_taxes*cO2_taxes_factor + subsidies*subsidies_factor

    # 4.- RV
    def compute(self):
        self.compute_depreciation()
        self.compute_impact_health()
        self.compute_external_factors()

        self.rv = (self.total_depreciation+self.total_impact_health+self.total_external_factors)


# %%
# Example
if __name__ == "__main__":
    from cosapp.drivers import RunOnce

    print("="*80)
    print("CosApp RV Calculator - Test Scenarios")
    print("="*80)
