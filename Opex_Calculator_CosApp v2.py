"""
CosApp System for calculating truck OPEX costs following exact diagram specifications.

===============================================================================
COLOR CODING FROM DIAGRAMS:
===============================================================================

[YELLOW] ARROWS = DATABASE PARAMETERS (Retrieved automatically)
   - National/regional standards and rates
   - Tax rates, toll prices, insurance rates, wages, energy prices
   - System looks these up based on country/vehicle/energy type
   
[ORANGE] ARROWS = USER INPUTS + DIGITAL TWIN OUTPUTS (Must be provided)
   - User Inputs: Vehicle-specific data (purchase cost, country, distance, etc.)
   - Digital Twin: Simulation outputs (consumption, emissions, fuel multiplier)
   
[GREEN] ARROWS = SYSTEM OUTPUTS (Calculated results)
   - O_Taxes, O_Tolls, O_Insurance, O_Crew, O_Energy, O_OPEX_Total

===============================================================================
INPUT CLASSIFICATION:
===============================================================================

[ORANGE] USER INPUTS (Orange - Vehicle-specific):
   + purchase_cost - What the vehicle costs
   + type_energy - Fuel type (diesel, electric, hybrid, etc.)
   + size_vehicle - Vehicle class (N1, N2, N3)
   + registration_country - Where it's registered
   + annual_distance_travel - km per year
   + departure_city - Starting location
   + arrival_city - Destination
   + RV - Residual value at end
   + N_years - Years of operation
   + team_count - Number of drivers (1 for trucks)
   + maintenance_cost - Annual maintenance

[ORANGE] DIGITAL TWIN OUTPUTS (Orange - From simulation):
   + consumption_energy - Actual consumption (kWh or liters)
   + fuel_multiplier - Efficiency factor
   + EF_CO2_diesel - CO2 emissions (kg/km)

[YELLOW] DATABASE PARAMETERS (Yellow - Automatic lookup):
   + price_energy_km - Energy cost per km
   + tax_energy_c_e - Energy tax by country & energy
   + tax_reg_c_k_L - Registration tax
   + tax_annual_c_k_L - Annual tax
   + regional_coefficient - Regional multiplier
   + tax_CO2_c_e - CO2 tax rate
   + B_env_c_k_e - Environmental bonus/malus
   + price_per_km (tolls) - Toll rates
   + insurance_rate_c_L_e_safety - Insurance rates
   + wage_of_crew_rank - Driver wages
   + energy_price_c_e - Fuel/electricity prices

===============================================================================
"""

import json
import sys
from cosapp.base import System
from cosapp.ports import Port

# Fix Windows console encoding for special characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class OPEXPort(Port):
    """Port for OPEX calculation inputs and outputs"""
    def setup(self):
        # User Inputs (Orange arrows in diagrams)
        self.add_variable('purchase_cost', dtype=float, desc='Purchase cost in EUR')
        self.add_variable('type_energy', dtype=str, desc='Type of energy')
        self.add_variable('size_vehicle', dtype=str, desc='Vehicle class (N1, N2, N3)')
        self.add_variable('registration_country', dtype=str, desc='Registration country')
        self.add_variable('annual_distance_travel', dtype=float, desc='Annual distance in km')
        self.add_variable('departure_city', dtype=str, desc='Departure city')
        self.add_variable('arrival_city', dtype=str, desc='Arrival city')
        self.add_variable('RV', dtype=float, desc='Residual Value in EUR')
        self.add_variable('N_years', dtype=float, desc='Number of years')
        self.add_variable('team_count', dtype=int, desc='Number of drivers (always 1 for trucks)')
        self.add_variable('maintenance_cost', dtype=float, desc='Annual maintenance cost in EUR')
        
        # Digital Twin Simulation Outputs (Orange arrows from DTS)
        self.add_variable('consumption_energy', dtype=float, desc='Energy consumption (kWh or liters)')
        self.add_variable('fuel_multiplier', dtype=float, desc='Fuel multiplier from DTS')
        self.add_variable('EF_CO2_diesel', dtype=float, desc='CO2 emission factor kg/km')
        
        # Outputs
        self.add_variable('o_taxes', dtype=float, desc='Total annual taxes in EUR')
        self.add_variable('o_tolls', dtype=float, desc='Total tolls cost in EUR')
        self.add_variable('o_insurance', dtype=float, desc='Total insurance cost in EUR')
        self.add_variable('o_crew', dtype=float, desc='Total crew cost in EUR')
        self.add_variable('o_energy', dtype=float, desc='Total energy cost in EUR')
        self.add_variable('o_opex_total', dtype=float, desc='Total OPEX in EUR')


class TruckOPEXCalculator(System):
    """
    CosApp System for calculating truck OPEX costs following the exact diagram specifications.
    
    Color coding from diagrams:
    - YELLOW arrows: Database parameters
    - ORANGE arrows: User inputs or Digital Twin outputs
    - GREEN arrows: System outputs
    
    OPEX Components:
    - O_taxes: Based on consumption, taxes, emissions, and environmental bonuses
    - O_tolls: Distance-based toll costs
    - O_insurance: Insurance based on vehicle value
    - O_crew: Driver wages
    - O_energy: Energy consumption costs
    """
    
    def __init__(self, name, db_path="DATA.JSON"):
        """Initialize with database path."""
        super().__init__(name)
        self._db_path = db_path
        self.setup(db_path)
    
    def setup(self, db_path: str = "DATA.JSON"):
        """
        Setup the system with database and ports.
        
        Args:
            db_path: Path to the JSON database file with realistic OPEX parameters
        """
        # Load database
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        # Store as private attribute
        object.__setattr__(self, '_countries_data', 
                          {c['country']: c['opex_database'] for c in db_data['countries']})
        object.__setattr__(self, '_db_metadata', {
            'description': db_data.get('description', ''),
            'source_note': db_data.get('source_note', ''),
            'references': db_data.get('references', {})
        })
        
        # Add port
        self.add_inward('opex', OPEXPort, desc='OPEX calculation port')
        
        # USER INPUTS (Orange arrows)
        self.add_inward('purchase_cost', 150000.0, desc='Purchase cost in EUR')
        self.add_inward('type_energy', 'diesel', dtype=str, desc='Type of energy')
        self.add_inward('size_vehicle', 'N3', dtype=str, desc='Vehicle class')
        self.add_inward('registration_country', 'France', dtype=str, desc='Registration country')
        self.add_inward('annual_distance_travel', 80000.0, desc='Annual distance in km')
        self.add_inward('departure_city', 'Paris', dtype=str, desc='Departure city')
        self.add_inward('arrival_city', 'Lyon', dtype=str, desc='Arrival city')
        self.add_inward('RV', 50000.0, desc='Residual Value in EUR')
        self.add_inward('N_years', 1.0, desc='Number of years')
        self.add_inward('team_count', 1, desc='Number of drivers')
        self.add_inward('maintenance_cost', 5000.0, desc='Annual maintenance in EUR')
        
        # DIGITAL TWIN SIMULATION OUTPUTS (Orange arrows from DTS)
        self.add_inward('consumption_energy', 28000.0, desc='Energy consumption kWh or liters')
        self.add_inward('fuel_multiplier', 1.0, desc='Fuel multiplier from DTS')
        self.add_inward('EF_CO2_diesel', 0.85, desc='CO2 emission factor kg/km')
        
        # DATABASE PARAMETERS (stored internally, Yellow arrows)
        # These are retrieved from the database in compute methods
        
        # OUTPUTS (Green arrows)
        self.add_outward('o_taxes', 0.0, desc='Total annual taxes in EUR')
        self.add_outward('o_tolls', 0.0, desc='Total tolls cost in EUR')
        self.add_outward('o_insurance', 0.0, desc='Total insurance cost in EUR')
        self.add_outward('o_crew', 0.0, desc='Total crew cost in EUR')
        self.add_outward('o_energy', 0.0, desc='Total energy cost in EUR')
        self.add_outward('o_opex_total', 0.0, desc='Total OPEX in EUR')
    
    # ==================== DATABASE ACCESS METHODS ====================
    
    def get_db_params(self, country: str, category: str):
        """Get database parameters for a specific category."""
        if country not in self._countries_data:
            raise ValueError(f"Country '{country}' not found in database")
        return self._countries_data[country][category]
    
    # ==================== O_TAXES CALCULATION ====================
    
    def compute_o_taxes(self):
        """
        Compute O_taxes following Fig. 4.1 diagram.
        
        Formula from report:
        O_taxes = consumption_energy × price_energy_km × tax_energy × fuel_multiplier × 
                  EF_CO2 × tax_CO2 × regional_coefficient + tax_reg + tax_annual + B_env
        
        Inputs (Orange):
        - purchase_cost (P)
        - type_energy
        - size_vehicle
        - registration_country
        - annual_distance_travel (D)
        - departure_city
        - arrival_city
        - consumption_energy (from DTS)
        - fuel_multiplier (from DTS)
        - EF_CO2_diesel (from DTS)
        
        Database (Yellow):
        - price_energy_km
        - tax_energy
        - tax_reg
        - tax_annual
        - regional_coefficient
        - tax_CO2
        - B_env
        
        Output (Green):
        - O_Taxes
        """
        taxes_db = self.get_db_params(self.registration_country, 'taxes')
        
        # Get database parameters (Yellow arrows)
        price_energy_km = taxes_db['price_energy_km']
        tax_energy = taxes_db['tax_energy_c_e'].get(self.type_energy, 1.0)
        tax_reg = taxes_db['tax_reg_c_k_L'].get(self.size_vehicle, 0.0)
        tax_annual = taxes_db['tax_annual_c_k_L'].get(self.size_vehicle, 0.0)
        regional_coefficient = taxes_db['regional_coefficient']
        tax_CO2 = taxes_db['tax_CO2_c_e']
        B_env = taxes_db['B_env_c_k_e'].get(self.type_energy, 0.0)
        
        # Calculate O_taxes
        variable_taxes = (self.consumption_energy * price_energy_km * tax_energy * 
                         self.fuel_multiplier * self.EF_CO2_diesel * tax_CO2 * 
                         regional_coefficient)
        
        fixed_taxes = tax_reg + tax_annual + B_env
        
        self.o_taxes = variable_taxes + fixed_taxes
    
    # ==================== O_TOLLS CALCULATION ====================
    
    def compute_o_tolls(self):
        """
        Compute O_tolls following Fig. 4.3 diagram.
        
        Formula: O_access_costs = price_per_km × distance
        
        Inputs (Orange):
        - distance (annual_distance_travel)
        - country (registration_country)
        - type_vehicle (size_vehicle)
        - type_of_energy (type_energy)
        
        Database (Yellow):
        - price_per_km
        
        Output (Green):
        - O_access_costs (o_tolls)
        """
        tolls_db = self.get_db_params(self.registration_country, 'tolls')
        
        # Get price per km from database (Yellow arrow)
        if self.size_vehicle not in tolls_db['price_per_km']:
            raise ValueError(f"Vehicle class '{self.size_vehicle}' not found in tolls database")
        
        if self.type_energy not in tolls_db['price_per_km'][self.size_vehicle]:
            raise ValueError(f"Energy type '{self.type_energy}' not found for vehicle class")
        
        price_per_km = tolls_db['price_per_km'][self.size_vehicle][self.type_energy]
        
        # Calculate O_tolls
        self.o_tolls = price_per_km * self.annual_distance_travel
    
    # ==================== O_INSURANCE CALCULATION ====================
    
    def compute_o_insurance(self):
        """
        Compute O_insurance following Fig. 4.5 diagram.
        
        Formula: O_insurance = insurance_percentage × (purchase_price - RV)
        
        Inputs (Orange):
        - purchase_price
        - RV
        
        Database (Yellow):
        - insurance_rate(c, L, e, safety_class)
        
        Output (Green):
        - O_insurance
        """
        insurance_db = self.get_db_params(self.registration_country, 'insurance')
        
        # Get insurance rate from database (Yellow arrow)
        if self.type_energy not in insurance_db['insurance_rate_c_L_e_safety']:
            raise ValueError(f"Energy type '{self.type_energy}' not found in insurance database")
        
        insurance_rate = insurance_db['insurance_rate_c_L_e_safety'][self.type_energy]
        
        # Calculate O_insurance
        self.o_insurance = insurance_rate * (self.purchase_cost - self.RV)
    
    # ==================== O_CREW CALCULATION ====================
    
    def compute_o_crew(self):
        """
        Compute O_crew following Fig. 4.6 diagram.
        
        Formula: O_crew = wage_of_driver × N
        
        Inputs (Orange):
        - N (N_years)
        - registration_country
        - team (team_count) - always 1 for trucks
        
        Database (Yellow):
        - wage_of_crew (wage_of_driver)
        
        Output (Green):
        - O_crew
        """
        crew_db = self.get_db_params(self.registration_country, 'crew')
        
        # Get driver wage from database (Yellow arrow)
        wage_of_driver = crew_db['wage_of_crew_rank']['driver']
        
        # Calculate O_crew (for trucks, team_count is always 1)
        self.o_crew = wage_of_driver * self.N_years * self.team_count
    
    # ==================== O_ENERGY CALCULATION ====================
    
    def compute_o_energy(self):
        """
        Compute O_energy following Fig. 4.7 diagram.
        
        Formula: O_energy = consumption_energy × energy_price × number_vehicles × country
        
        Inputs (Orange from DTS):
        - Fuel consumption (consumption_energy)
        - Power (implicit in consumption)
        - Time (implicit in consumption)
        
        Inputs (Orange from User):
        - Country (registration_country)
        - Number vehicles (1 for single vehicle)
        
        Database (Yellow):
        - Energy_price
        
        Output (Green via Consumption block then energy block):
        - O_kWh (consumption_energy)
        - O_energy
        """
        energy_db = self.get_db_params(self.registration_country, 'energy')
        
        # Get energy price from database (Yellow arrow)
        if self.type_energy not in energy_db['energy_price_c_e']:
            raise ValueError(f"Energy type '{self.type_energy}' not found in energy database")
        
        energy_price = energy_db['energy_price_c_e'][self.type_energy]
        
        # Calculate O_energy
        # For a single vehicle, number_vehicles = 1
        self.o_energy = self.consumption_energy * energy_price
    
    # ==================== MAIN COMPUTE ====================
    
    def compute(self):
        """
        Main compute method - calculates all OPEX components.
        Total OPEX = O_taxes + O_tolls + O_insurance + O_crew + O_energy + O_maintenance
        """
        # Compute all OPEX components
        self.compute_o_taxes()
        self.compute_o_tolls()
        self.compute_o_insurance()
        self.compute_o_crew()
        self.compute_o_energy()
        
        # Calculate total OPEX
        self.o_opex_total = (self.o_taxes + 
                            self.o_tolls + 
                            self.o_insurance + 
                            self.o_crew + 
                            self.o_energy + 
                            self.maintenance_cost)
    
    # ==================== UTILITY METHODS ====================
    
    def get_available_countries(self) -> list:
        """Get list of available countries in the database."""
        return list(self._countries_data.keys())
    
    def get_available_energy_types(self) -> list:
        """Get list of available energy types."""
        return ['diesel', 'electric', 'hybrid', 'hydrogen_fuel_cell', 
                'hydrogen_h2', 'cng', 'lng']
    
    def print_database_info(self):
        """Print database metadata and references."""
        print("\n" + "="*80)
        print("DATABASE INFORMATION - REALISTIC OPEX PARAMETERS")
        print("="*80)
        print(f"\nDescription: {self._db_metadata.get('description', 'N/A')}")
        print(f"\nSource Note: {self._db_metadata.get('source_note', 'N/A')}")
        
        print("\n--- DATA REFERENCES ---")
        refs = self._db_metadata.get('references', {})
        if refs:
            for key, url in refs.items():
                print(f"  * {key}:")
                print(f"    {url}")
        else:
            print("  No references available")
        
        print("\n--- AVAILABLE COUNTRIES ---")
        for country in self.get_available_countries():
            country_data = self._countries_data[country]
            driver_wage = country_data['crew']['wage_of_crew_rank']['driver']
            diesel_price = country_data['energy']['energy_price_c_e']['diesel']
            print(f"  * {country}:")
            print(f"    - Driver wage: {driver_wage:.2f} EUR/year")
            print(f"    - Diesel price: {diesel_price:.2f} EUR/liter")
        
        print("="*80 + "\n")
    
    def validate_inputs(self):
        """
        Validate that all required inputs are provided.
        Returns a dict with status and missing inputs if any.
        """
        missing = []
        warnings = []
        
        # Check USER INPUTS (Orange arrows)
        if self.purchase_cost <= 0:
            missing.append("purchase_cost must be > 0")
        if self.type_energy not in self.get_available_energy_types():
            missing.append(f"type_energy must be one of {self.get_available_energy_types()}")
        if self.size_vehicle not in ['N1', 'N2', 'N3']:
            missing.append("size_vehicle must be N1, N2, or N3")
        if self.registration_country not in self.get_available_countries():
            missing.append(f"registration_country must be one of {self.get_available_countries()}")
        if self.annual_distance_travel <= 0:
            missing.append("annual_distance_travel must be > 0")
        if self.RV < 0 or self.RV >= self.purchase_cost:
            warnings.append("RV should be between 0 and purchase_cost")
        if self.N_years <= 0:
            missing.append("N_years must be > 0")
        
        # Check DIGITAL TWIN OUTPUTS (Orange arrows from simulation)
        if self.consumption_energy <= 0:
            missing.append("consumption_energy must be > 0 (from Digital Twin)")
        if self.fuel_multiplier < 0:
            missing.append("fuel_multiplier must be >= 0 (from Digital Twin)")
        if self.EF_CO2_diesel < 0:
            missing.append("EF_CO2_diesel must be >= 0 (from Digital Twin)")
        
        return {
            'valid': len(missing) == 0,
            'missing': missing,
            'warnings': warnings
        }
    
    def print_input_summary(self):
        """Print a summary of all inputs for verification."""
        print("\n" + "="*80)
        print("INPUT SUMMARY - PLEASE VERIFY")
        print("="*80)
        print("\n[ORANGE] USER INPUTS (Orange arrows):")
        print(f"  * Purchase Cost: {self.purchase_cost:.2f} EUR")
        print(f"  * Energy Type: {self.type_energy}")
        print(f"  * Vehicle Class: {self.size_vehicle}")
        print(f"  * Country: {self.registration_country}")
        print(f"  * Annual Distance: {self.annual_distance_travel:.2f} km")
        print(f"  * Route: {self.departure_city} -> {self.arrival_city}")
        print(f"  * Residual Value: {self.RV:.2f} EUR")
        print(f"  * Operational Years: {self.N_years:.1f}")
        print(f"  * Number of Drivers: {self.team_count}")
        print(f"  * Maintenance Cost: {self.maintenance_cost:.2f} EUR/year")
        
        print("\n[ORANGE] DIGITAL TWIN OUTPUTS (Orange arrows from simulation):")
        print(f"  * Energy Consumption: {self.consumption_energy:.2f} kWh or liters")
        print(f"  * Fuel Multiplier: {self.fuel_multiplier:.2f}")
        print(f"  * CO2 Emissions: {self.EF_CO2_diesel:.3f} kg/km")
        
        print("\n[YELLOW] DATABASE PARAMETERS (Yellow arrows - automatic):")
        print(f"  + Will be retrieved from database for {self.registration_country}")
        print(f"  + Based on vehicle class {self.size_vehicle} and energy {self.type_energy}")
        
        # Validate
        validation = self.validate_inputs()
        if validation['valid']:
            print("\n[OK] All inputs are valid!")
        else:
            print("\n[ERROR] VALIDATION ERRORS:")
            for error in validation['missing']:
                print(f"  X {error}")
        
        if validation['warnings']:
            print("\n[WARNING] WARNINGS:")
            for warning in validation['warnings']:
                print(f"  ! {warning}")
        
        print("="*80 + "\n")
    
    def print_results(self):
        """Print calculation results in a formatted way."""
        print("\n" + "="*80)
        print("TRUCK OPEX CALCULATION RESULTS")
        print("="*80)
        print(f"Country: {self.registration_country}")
        print(f"Vehicle Class: {self.size_vehicle}")
        print(f"Energy Type: {self.type_energy}")
        print(f"Annual Distance: {self.annual_distance_travel:.2f} km")
        print(f"Purchase Cost: {self.purchase_cost:.2f} EUR")
        print(f"Residual Value: {self.RV:.2f} EUR")
        print(f"Number of Years: {self.N_years:.1f}")
        print("-"*80)
        
        print("\n--- O_TAXES (Annual Operating Taxes) ---")
        print(f"Consumption Energy: {self.consumption_energy:.2f} kWh or liters")
        print(f"Fuel Multiplier: {self.fuel_multiplier:.2f}")
        print(f"CO2 Emission Factor: {self.EF_CO2_diesel:.3f} kg/km")
        print(f"→ TOTAL O_TAXES: {self.o_taxes:.2f} EUR/year")
        
        print("\n--- O_TOLLS (Road Tolls) ---")
        print(f"Distance: {self.annual_distance_travel:.2f} km")
        print(f"→ TOTAL O_TOLLS: {self.o_tolls:.2f} EUR")
        
        print("\n--- O_INSURANCE ---")
        print(f"Insured Value: {(self.purchase_cost - self.RV):.2f} EUR")
        print(f"→ TOTAL O_INSURANCE: {self.o_insurance:.2f} EUR/year")
        
        print("\n--- O_CREW (Driver Wages) ---")
        print(f"Number of Drivers: {self.team_count}")
        print(f"→ TOTAL O_CREW: {self.o_crew:.2f} EUR")
        
        print("\n--- O_ENERGY (Fuel/Electricity Costs) ---")
        print(f"Energy Consumption: {self.consumption_energy:.2f} kWh or liters")
        print(f"→ TOTAL O_ENERGY: {self.o_energy:.2f} EUR")
        
        print("\n--- O_MAINTENANCE ---")
        print(f"Annual Maintenance: {self.maintenance_cost:.2f} EUR/year")
        
        print("\n" + "="*80)
        print(f"TOTAL OPEX: {self.o_opex_total:.2f} EUR")
        print("="*80 + "\n")
    
    def save_results_to_file(self, filename: str = "opex_results.txt"):
        """Save calculation results to a text file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("TRUCK OPEX CALCULATION RESULTS\n")
            f.write("="*80 + "\n")
            f.write(f"Country: {self.registration_country}\n")
            f.write(f"Vehicle Class: {self.size_vehicle}\n")
            f.write(f"Energy Type: {self.type_energy}\n")
            f.write(f"Annual Distance: {self.annual_distance_travel:.2f} km\n")
            f.write(f"Purchase Cost: {self.purchase_cost:.2f} EUR\n")
            f.write(f"Residual Value: {self.RV:.2f} EUR\n")
            f.write(f"Number of Years: {self.N_years:.1f}\n")
            f.write("-"*80 + "\n\n")
            
            f.write("--- O_TAXES (Annual Operating Taxes) ---\n")
            f.write(f"→ TOTAL O_TAXES: {self.o_taxes:.2f} EUR/year\n\n")
            
            f.write("--- O_TOLLS (Road Tolls) ---\n")
            f.write(f"→ TOTAL O_TOLLS: {self.o_tolls:.2f} EUR\n\n")
            
            f.write("--- O_INSURANCE ---\n")
            f.write(f"→ TOTAL O_INSURANCE: {self.o_insurance:.2f} EUR/year\n\n")
            
            f.write("--- O_CREW (Driver Wages) ---\n")
            f.write(f"→ TOTAL O_CREW: {self.o_crew:.2f} EUR\n\n")
            
            f.write("--- O_ENERGY (Fuel/Electricity Costs) ---\n")
            f.write(f"→ TOTAL O_ENERGY: {self.o_energy:.2f} EUR\n\n")
            
            f.write("--- O_MAINTENANCE ---\n")
            f.write(f"Annual Maintenance: {self.maintenance_cost:.2f} EUR/year\n\n")
            
            f.write("="*80 + "\n")
            f.write(f"TOTAL OPEX: {self.o_opex_total:.2f} EUR\n")
            f.write("="*80 + "\n")
        
        print(f"\n✅ Results saved to: {filename}")


# Example usage and test scenarios with REALISTIC data
if __name__ == "__main__":
    from cosapp.drivers import RunOnce
    
    print("="*80)
    print("CosApp Truck OPEX Calculator - REALISTIC SCENARIOS")
    print("Using real-world data from EU sources and industry benchmarks")
    print("="*80)
    
    # Create first system to show database info
    sys_info = TruckOPEXCalculator('info', db_path='DATA.JSON')
    sys_info.print_database_info()
    
    # ========================================================================
    # SCENARIO 1: Heavy Diesel Truck in France (Realistic Long-haul)
    # ========================================================================
    print("\n" + "#"*80)
    print("### SCENARIO 1: Heavy Diesel Truck in France (N3, Long-haul) ###")
    print("### Based on: MDPI Slovakia study + French driver wages (Le Figaro) ###")
    print("#"*80)
    
    sys1 = TruckOPEXCalculator('opex_diesel_fr', db_path='DATA.JSON')
    
    # User inputs (Orange arrows) - REALISTIC VALUES
    sys1.purchase_cost = 120000.0  # Typical N3 truck price
    sys1.type_energy = 'diesel'
    sys1.size_vehicle = 'N3'
    sys1.registration_country = 'France'
    sys1.annual_distance_travel = 100000.0  # Average long-haul
    sys1.departure_city = 'Paris'
    sys1.arrival_city = 'Marseille'
    sys1.RV = 30000.0  # ~25% after 5 years
    sys1.N_years = 5.0
    sys1.team_count = 1
    sys1.maintenance_cost = 6000.0  # Realistic annual maintenance
    
    # Digital Twin Simulation outputs (Orange arrows from DTS) - REALISTIC
    # Consumption: ~35 L/100km × 100,000 km = 35,000 liters/year
    sys1.consumption_energy = 35000.0  # liters diesel per year
    sys1.fuel_multiplier = 1.0
    sys1.EF_CO2_diesel = 2.65  # kg CO2/liter diesel (standard)
    
    # Show input summary and validate
    sys1.print_input_summary()
    
    driver1 = sys1.add_driver(RunOnce('run1'))
    sys1.run_drivers()
    sys1.print_results()
    sys1.save_results_to_file("scenario1_realistic_diesel_france.txt")
    
    # ========================================================================
    # SCENARIO 2: Electric Medium Truck in Germany (Urban delivery)
    # ========================================================================
    print("\n" + "#"*80)
    print("### SCENARIO 2: Electric Medium Truck in Germany (N2, Urban) ###")
    print("### Based on: arXiv TCO model + EU electricity prices ###")
    print("#"*80)
    
    sys2 = TruckOPEXCalculator('opex_electric_de', db_path='DATA.JSON')
    
    # User inputs (Orange arrows) - REALISTIC VALUES
    sys2.purchase_cost = 85000.0  # Electric N2 with subsidy consideration
    sys2.type_energy = 'electric'
    sys2.size_vehicle = 'N2'
    sys2.registration_country = 'Germany'
    sys2.annual_distance_travel = 30000.0  # Urban delivery range
    sys2.departure_city = 'Berlin'
    sys2.arrival_city = 'Hamburg'
    sys2.RV = 35000.0  # ~40% retention for electric
    sys2.N_years = 5.0
    sys2.team_count = 1
    sys2.maintenance_cost = 2500.0  # Lower for electric
    
    # Digital Twin Simulation outputs (Orange arrows from DTS) - REALISTIC
    # Consumption: ~1.2 kWh/km × 30,000 km = 36,000 kWh/year
    sys2.consumption_energy = 36000.0  # kWh per year
    sys2.fuel_multiplier = 0.3  # Much cleaner than diesel
    sys2.EF_CO2_diesel = 0.4  # kg CO2/kWh (grid mix Germany)
    
    driver2 = sys2.add_driver(RunOnce('run2'))
    sys2.run_drivers()
    sys2.print_results()
    sys2.save_results_to_file("scenario2_realistic_electric_germany.txt")
    
    # ========================================================================
    # SCENARIO 3: Hydrogen Fuel Cell Heavy Truck in Spain (Green logistics)
    # ========================================================================
    print("\n" + "#"*80)
    print("### SCENARIO 3: Hydrogen Fuel Cell Heavy Truck in Spain (N3) ###")
    print("#"*80)
    
    sys3 = TruckOPEXCalculator('opex_h2_es', db_path='DATA.JSON')
    
    # User inputs (Orange arrows)
    sys3.purchase_cost = 220000.0  # Higher initial cost
    sys3.type_energy = 'hydrogen_fuel_cell'
    sys3.size_vehicle = 'N3'
    sys3.registration_country = 'Spain'
    sys3.annual_distance_travel = 100000.0
    sys3.departure_city = 'Madrid'
    sys3.arrival_city = 'Barcelona'
    sys3.RV = 70000.0
    sys3.N_years = 5.0
    sys3.team_count = 1
    sys3.maintenance_cost = 8500.0
    
    # Digital Twin Simulation outputs (Orange arrows from DTS)
    sys3.consumption_energy = 3500.0  # kg H2 per year
    sys3.fuel_multiplier = 0.4  # Clean technology
    sys3.EF_CO2_diesel = 0.0  # Zero emissions
    
    driver3 = sys3.add_driver(RunOnce('run3'))
    sys3.run_drivers()
    sys3.print_results()
    sys3.save_results_to_file("scenario3_hydrogen_spain.txt")
    
    # ========================================================================
    # SCENARIO 4: Hybrid Light Truck in Italy (Mixed usage)
    # ========================================================================
    print("\n" + "#"*80)
    print("### SCENARIO 4: Hybrid Light Truck in Italy (N1, Mixed) ###")
    print("#"*80)
    
    sys4 = TruckOPEXCalculator('opex_hybrid_it', db_path='DATA.JSON')
    
    # User inputs (Orange arrows)
    sys4.purchase_cost = 55000.0
    sys4.type_energy = 'hybrid'
    sys4.size_vehicle = 'N1'
    sys4.registration_country = 'Italy'
    sys4.annual_distance_travel = 45000.0
    sys4.departure_city = 'Rome'
    sys4.arrival_city = 'Milan'
    sys4.RV = 22000.0
    sys4.N_years = 5.0
    sys4.team_count = 1
    sys4.maintenance_cost = 4000.0
    
    # Digital Twin Simulation outputs (Orange arrows from DTS)
    sys4.consumption_energy = 3600.0  # liters equivalent per year
    sys4.fuel_multiplier = 0.6  # Cleaner than diesel
    sys4.EF_CO2_diesel = 1.85  # kg CO2/liter
    
    driver4 = sys4.add_driver(RunOnce('run4'))
    sys4.run_drivers()
    sys4.print_results()
    sys4.save_results_to_file("scenario4_hybrid_italy.txt")
    
    # ========================================================================
    # COMPARISON SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("COMPREHENSIVE COMPARISON SUMMARY - ALL SCENARIOS")
    print("="*80)
    print(f"{'Scenario':<35} {'Total OPEX':>12} {'Energy':>12} {'Taxes':>12} {'Tolls':>12}")
    print("-"*80)
    print(f"{'1. Diesel N3 France':<35} {sys1.o_opex_total:>9.2f} EUR {sys1.o_energy:>9.2f} {sys1.o_taxes:>9.2f} {sys1.o_tolls:>9.2f}")
    print(f"{'2. Electric N2 Germany':<35} {sys2.o_opex_total:>9.2f} EUR {sys2.o_energy:>9.2f} {sys2.o_taxes:>9.2f} {sys2.o_tolls:>9.2f}")
    print(f"{'3. H2 Fuel Cell N3 Spain':<35} {sys3.o_opex_total:>9.2f} EUR {sys3.o_energy:>9.2f} {sys3.o_taxes:>9.2f} {sys3.o_tolls:>9.2f}")
    print(f"{'4. Hybrid N1 Italy':<35} {sys4.o_opex_total:>9.2f} EUR {sys4.o_energy:>9.2f} {sys4.o_taxes:>9.2f} {sys4.o_tolls:>9.2f}")
    print("="*80)
    
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print("+ All calculations follow exact diagram specifications")
    print("+ [YELLOW] arrows = Database parameters (retrieved automatically)")
    print("+ [ORANGE] arrows = User inputs + Digital Twin outputs (must provide)")
    print("+ [GREEN] arrows = System outputs (calculated results)")
    print("+ Results saved to individual text files for each scenario")
    print("\n" + "="*80)
    print("DATABASE vs USER INPUTS - CLEAR SEPARATION")
    print("="*80)
    print("\n[YELLOW] FROM DATABASE (Yellow - Automatic):")
    print("  * Tax rates, toll prices, insurance rates")
    print("  * National wage standards, energy prices")
    print("  * Environmental bonuses/maluses")
    print("  -> System retrieves based on country/vehicle/energy type")
    print("\n[ORANGE] FROM USER (Orange - Manual Input):")
    print("  * Purchase cost, vehicle specs, registration country")
    print("  * Annual distance, route, operational years")
    print("  * Residual value, maintenance costs")
    print("  -> User must provide these specific values")
    print("\n[ORANGE] FROM DIGITAL TWIN (Orange - Simulation Output):")
    print("  * Energy consumption (actual usage)")
    print("  * Fuel multiplier (efficiency)")
    print("  * CO2 emissions (environmental impact)")
    print("  -> Comes from vehicle simulation, not user estimate")
    print("="*80)