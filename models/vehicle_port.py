from cosapp.base import Port
from datetime import datetime

class VehiclePropertiesPort(Port):
    '''
    Port for Vehicle Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        # -------------------- USER INPUTS --------------------
        # Common inputs
        self.add_variable('type_vehicle', dtype=str, desc='Vehicle type: Truck or Ship', value='truck')
        self.add_variable('type_energy', dtype=str, desc='Energy type: diesel, electric, hybrid, hydrogen_fuel_cell, hydrogen_h2, cng, lng', value='DIESEL')
        self.add_variable('purchase_cost', dtype=float, desc='Initial purchase cost', value=0.0)
        self.add_variable('registration_country', dtype=str, desc='Registration country of the vehicle', value='France')
        
        self.add_variable('travel_measure', dtype=float, desc='Total Distance (km) or hours (h)', value=0.0)
        self.add_variable('maintenance_cost', dtype=float, desc='Total maintenance cost incurred', value=0.0)
        
        self.add_variable('minimum_fuel_consumption', dtype=float, desc='SFC (g/kWh)', value=250.0)
        self.add_variable('consumption_real', dtype=float, desc='Real consumption (kWh/km or kg/100km)', value=0.0)
        self.add_variable('C_bat_kwh', dtype=float, desc='Battery capacity (kWh)', value=1.0)
        self.add_variable('autonomy', dtype=float, desc="Autonomy (km)", value=1.0)
        self.add_variable('utility_factor', dtype=float, desc='Electric fraction for hybrids', value=0.0)
        
        self.add_variable('E_annual_kwh', dtype=float, desc='Annual energy consumption (kWh)', value=0.0)
        self.add_variable('DoD', dtype=float, desc='Depth of discharge', value=0.8)
        self.add_variable('S_slow', dtype=float, desc='Proportion slow charging', value=0.0)
        self.add_variable('S_fast', dtype=float, desc='Proportion fast charging', value=0.0)
        self.add_variable('S_ultra', dtype=float, desc='Proportion ultra-fast charging', value=0.0)
        
        self.add_variable('powertrain_model_year', dtype=int, desc='Powertrain model year', value=2020)
        
        self.add_variable('warranty', dtype=float, desc='Warranty duration (years or km)', value=5.0)
        self.add_variable('type_warranty', dtype=str, desc='Type of warranty: years or km', value='years')
        self.add_variable('year_purchase', dtype=int, desc='Year of purchase', value=2020)
        
        self.add_variable('current_year', dtype=int, desc='Current year', value=datetime.now().year)
        self.add_variable('vehicle_number', dtype=int, desc='Numbers of vehicle', value=1)

        # CAPEX INPUTS
        self.add_variable("vehicle_id", dtype=int, desc="Vehicle ID in fleet")
        self.add_variable("vehicle_weight_class", dtype=str, desc="Weight class", value="light")
        self.add_variable("country", dtype=str, desc="Country code", value="France") # Should be the same as registration_country
        self.add_variable("year", dtype=int, desc="Year for subsidies calculation", value=2025) # Should be the same as current_year
        # Vehicle acquisition
        self.add_variable("is_new", dtype=bool, desc="True if buying new vehicle", value=True)
        self.add_variable("owns_vehicle", dtype=bool, desc="True if already owns vehicle", value=False)
        self.add_variable("conversion_cost", dtype=float, desc="Conversion cost in EUR", value=0.0)
        self.add_variable("certification_cost", dtype=float, desc="Certification cost in EUR", value=0.0)
        # Fleet dictionary
        self.add_variable("vehicle_dict", {}, desc="Dictionary of vehicles with energy data")
        # Infrastructure parameters
        self.add_variable("n_slow", dtype=int, desc="Number of slow chargers", value=None)
        self.add_variable("n_fast", dtype=int, desc="Number of fast chargers", value=None)
        self.add_variable("n_ultra", dtype=int, desc="Number of ultra-fast chargers", value=None)
        self.add_variable("n_stations", dtype=int, desc="Number of stations", value=1)
        self.add_variable("smart_charging_enabled", dtype=bool, desc="Smart charging enabled", value=False)
        # Financing
        self.add_variable("loan_years", dtype=int, desc="Number of years for loan", value=10)


        # SHIP OPEX
        self.add_variable("country_oper", dtype=str, desc="Country of operation", value="France")
        self.add_variable("ship_class", dtype=str,
            desc=(
                "Ship class key used in DB "
                "(ro_pax_small, fishing_large, ctv_medium, ro_pax, small, medium, large, ctv...)"
            ),
            value="small"
        )
        self.add_variable("length", dtype=float, desc="Ship length in meters", value=120.0)
        self.add_variable("safety_class", dtype=str, desc="Safety class", value="A")
        self.add_variable(
            "annual_distance", dtype=float, desc="Annual distance travelled (km or nm)", value=20_000.0
        )

        # Gross tonnage
        self.add_variable("GT", dtype=float, desc="Gross tonnage (GT) of the ship", value=0.0)

        # Ports / trips
        self.add_variable("n_trips_per_year", dtype=float, desc="Number of trips per year", value=10.0)
        self.add_variable("days_per_trip", dtype=float, desc="Number of days per trip", value=5.0)

        # Crew
        self.add_variable(
            "crew_list",
            value=[
                { "rank": "skipper",  "attribute": "ro_pax_large", "team_size": 1 },
                { "rank": "deckhand", "attribute": "ro_pax_large", "team_size": 10 },
                { "rank": "engineer", "attribute": "ro_pax_large", "team_size": 3 }
            ],
            desc="CREW: rank, attribute, team_size",
            dtype=list
        )

        self.add_variable("planning_horizon_years", dtype=float, desc="Number of years N", value=1.0)
        self.add_variable(
            "maintenance_cost_annual",
            dtype=float,
            desc="Annual maintenance cost in EUR (legacy)",
            value=100_000.0
        )
        

        # -------------------- DIGITAL TWIN / USER ENV (ORANGE) --------------------
        self.add_variable("I_energy", dtype=float, desc="Energy consumption per km (MWh/km or ton/km)", value=0.5)
        self.add_variable(
            "EF_CO2",
            dtype=float,
            desc="CO2 emission factor per unit of energy (kg CO2 / kWh or per ton)",
            value=0.27
        )
        self.add_variable(
            "NOxSOx_rate",
            dtype=float,
            desc="NOx/SOx emission per km (kg/km)",
            value=0.01
        )
        self.add_variable(
            "annual_energy_consumption_kWh",
            dtype=float,
            desc="Annual energy consumption retrieved from digital twin (kWh)",
            value=5_000_000.0
        )

        # fuel mass: inward in kg, converted to ton in formulas
        self.add_variable(
            "fuel_mass_kg",
            dtype=float,
            desc="Fuel mass used in a period (kg), provided by digital twin",
            value=0.0
        )

        # Opex Truck
        self.add_variable("size_vehicle", dtype=str, desc="Vehicle class (N1, N2, N3)", value="N3")
        self.add_variable("annual_distance_travel", dtype=float, desc="Annual distance in km", value=20_000.0)
        self.add_variable("RV", dtype=float, desc="Residual Value in EUR", value=45000.0)
        self.add_variable("N_years", dtype=float, desc="Number of years", value=5.0)
        self.add_variable("team_count", dtype=int, desc="Number of drivers", value=1)

        # Digital Twin Simulation Outputs
        self.add_variable("consumption_energy", dtype=float, desc="Energy consumption (kWh or liters)", value=42000.0)
        self.add_variable("fuel_multiplier", dtype=float, desc="Fuel multiplier from DTS", value=1.0)
