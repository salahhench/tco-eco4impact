"""
Residual Value (RV) Calculator - CoSApp Implementation
"""
import os
from cosapp.base import System
import json
import math
from models.vehicle_port import VehiclePropertiesPort
from models.country_port import CountryPropertiesPort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    def setup(self, type_vehicle: str = "trucks", db_path: str = None):
        # -------------------- LOAD DATABASE --------------------
        if db_path is None:
            db_folder = os.path.abspath(os.path.join(BASE_DIR, "..", "database"))
            if type_vehicle.lower() == "ship":
                db_path = os.path.join(db_folder, "db_ships.json")
            else:
                db_path = os.path.join(db_folder, "db_trucks.json")
        
        # Load database
        with open(db_path, 'r') as f:
            db_rv = json.load(f)

        object.__setattr__(self, '_countries_data',
                           {c['country']: c for c in db_rv['countries']})
        
        object.__setattr__(self, '_vehicles_data',db_rv['vehicle'])
        
        # # Add ports
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
        type_energy = vp.type_energy
        country = vp.registration_country
        number_of_vehicles = vp.vehicle_number

        # Depreciation components
        purchase_cost = vp.purchase_cost
        vehicle_age = vp.current_year - vp.year_purchase    

        # Parameters of database
        rate_per_year = self._countries_data[country]["depreciation"]["depreciation_rate_per_year"][type_energy]
        r_usage = self._countries_data[country]["depreciation"]["r_usage"][type_energy]
        rate_by_usage = r_usage
        coef_maintenance = self._countries_data[country]["depreciation"]["coef_depreciation_maintenance"][type_energy]

        dep_per_year = rate_per_year * vehicle_age
        dep_by_usage = rate_by_usage * vp.travel_measure
        dep_maintenance = coef_maintenance * vp.maintenance_cost


        # Total depreciation
        self.total_depreciation = purchase_cost - (dep_per_year + dep_by_usage + dep_maintenance)
        self.total_depreciation = self.total_depreciation*number_of_vehicles

    # 2.1.- PENALIZATION OF EFICIENCY
    def compute_eficiency(self):
        # Inputs
        vp = self.in_vehicle_properties
        type_energy = vp.type_energy
        

        # Depends of the type of energy:
        if type_energy in ["DIESEL", "BIO_DIESEL", "HVO" ,"E_DIESEL", "CNG", "LNG", "H2_ICE"]:
            minimum_fuel_consumption = vp.minimum_fuel_consumption
            heating_value = self._vehicles_data["heating_value"][type_energy]
            # ICE vehicles: η_f = 360S0 / (SFC * Q_HV)
            n_f = 3600/(minimum_fuel_consumption * heating_value)
        
        elif type_energy in ["BEV", "FCEV"]:
            # Electric/Fuel Cell: η_sys = consumption_benchmark / consumption_real
            consumption_real = vp.consumption_real
            battery_capacity = vp.C_bat_kwh
            autonomy = vp.autonomy

            consumption_benchmark = battery_capacity/autonomy

            if consumption_real>0:
                n_f = consumption_benchmark / consumption_real
            else:
                n_f = 0.85
        
        elif type_energy in ["HEV", "PHEV"]:
            # Hybrid: η_hybrid = 1 / [(α/η_EV) + (1-α)/η_ICE]
            utility_factor = vp.utility_factor

            # Part of ICE
            minimum_fuel_consumption = vp.minimum_fuel_consumption
            heating_value = self._vehicles_data["heating_value"][type_energy]
            # ICE vehicles: η_f = 360S0 / (SFC * Q_HV)
            n_ice = 3600/(minimum_fuel_consumption * heating_value)


            # Part of BEV
            consumption_real = vp.consumption_real
            battery_capacity = vp.C_bat_kwh
            autonomy = vp.autonomy

            consumption_benchmark = battery_capacity/autonomy

            if consumption_real>0:
                n_ev = consumption_benchmark / consumption_real
            else:
                n_ev = 0.85

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
        vp = self.in_vehicle_properties
        number_of_vehicles = vp.vehicle_number
        
        # Compute IMPACT HEALTH
        self.total_impact_health = (self.efficiency_penalty+self.obsolescence_penalty+self.charging_penalty+self.warranty_penalty)
        self.total_impact_health = self.total_impact_health*number_of_vehicles

    # 3.- EXTERNAL FACTORS
    def compute_external_factors(self):
        # Inputs
        cp = self.in_country_properties
        vp = self.in_vehicle_properties
        energy_price = cp.energy_price
        c02_taxes = cp.c02_taxes
        subsidies = cp.subsidies
        type_energy = vp.type_energy
        country = vp.registration_country
        number_of_vehicles = vp.vehicle_number


        # Parameters of database
        energy_price_factor = self._countries_data[country]["external_factors"]["energy_price_factor"][type_energy]
        cO2_taxes_factor = self._countries_data[country]["external_factors"]["CO2_taxes_factor"]
        subsidies_factor = self._countries_data[country]["external_factors"]["subsidies_factor"][type_energy]

        # Total external_factors
        self.total_external_factors = energy_price_factor*energy_price+ c02_taxes*cO2_taxes_factor + subsidies*subsidies_factor
        self.total_external_factors = self.total_external_factors*number_of_vehicles

    # 4.- RV
    def compute(self):
        try:
            self.compute_depreciation()
            self.compute_impact_health()
            self.compute_external_factors()

            self.rv = (self.total_depreciation/ self.total_impact_health+self.total_external_factors)
        except Exception as e:
            print(f"ERROR in RV compute: {e}")
