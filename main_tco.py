"""
Main TCO orchestrator for Eco4Impact / BoatTwin project.

Calls:
    * VehicleCAPEXCalculator (capex_calculator.py)
    * TruckOPEXCalculator / ShipOPEXCalculator (Opex_Calculator.py)
    * ResidualValueCalculator (rv_calculator.py)

Uses a GENERAL INPUT (user_inputs) with:
    asset_type: "truck" or "ship"
    powertrain_type, country, etc.

Calculates and displays:
    CAPEX, OPEX, RV and TCO_total example.
"""

from cosapp.drivers import RunOnce

# Import both OPEX calculators from the same file
from functions.Opex_Calculator import TruckOPEXCalculator, ShipOPEXCalculator
from functions.rv_calculator import ResidualValueCalculator
from functions.capex_calculator import VehicleCAPEXCalculator
from inputs.gen_truck_in import make_example_truck_electric_fleet , make_example_truck_diesel
from inputs.gen_ship_in import make_example_ship_electric,make_example_ship_diesel


# ======================================================================
# WRAPPER FUNCTIONS FOR EACH MODULE
# ======================================================================

def run_capex(capex_inputs: dict, asset_type: str) -> float:
    """
    Run CAPEX calculation for a vehicle.
    
    Args:
        capex_inputs: Dictionary with CAPEX parameters
        asset_type: "truck" or "ship"
        
    Returns:
        Annual CAPEX per vehicle
    """
    print("\n" + "="*80)
    print("RUNNING CAPEX CALCULATION")
    print("="*80)
    
    capex_data = capex_inputs.get("capex", {})
    
    # Initialize CAPEX system with vehicle type
    sys_capex = VehicleCAPEXCalculator("capex_global", vehicle_type=asset_type)
    
    # -------------------- MAIN USER INPUTS --------------------
    sys_capex.in_vehicle_properties.type_vehicle = capex_data.get("powertrain_type", "DIESEL")
    sys_capex.in_vehicle_properties.type_energy = capex_data.get("powertrain_type", "DIESEL")
    sys_capex.in_vehicle_properties.vehicle_number = capex_data.get("vehicle_number", 1)
    sys_capex.in_vehicle_properties.vehicle_id = capex_data.get("vehicle_id", 1)
    sys_capex.in_vehicle_properties.vehicle_weight_class = capex_data.get("vehicle_weight_class", "light")
    sys_capex.in_vehicle_properties.registration_country = capex_data.get("country", "France")
    sys_capex.in_vehicle_properties.year = capex_data.get("year", 2025)
    
    print(f"Asset Type: {asset_type.upper()}")
    print(f"Powertrain: {sys_capex.in_vehicle_properties.type_energy}")
    print(f"Weight Class: {sys_capex.in_vehicle_properties.vehicle_weight_class}")
    print(f"Country: {sys_capex.in_vehicle_properties.registration_country}")
    print(f"Fleet Size: {sys_capex.in_vehicle_properties.vehicle_number} vehicles")
    
    # -------------------- VEHICLE ACQUISITION --------------------
    sys_capex.in_vehicle_properties.is_new = capex_data.get("is_new", True)
    sys_capex.in_vehicle_properties.owns_vehicle = capex_data.get("owns_vehicle", False)
    sys_capex.in_vehicle_properties.purchase_cost = capex_data.get("purchase_price", 0.0)
    sys_capex.in_vehicle_properties.conversion_cost = capex_data.get("conversion_cost", 0.0)
    sys_capex.in_vehicle_properties.certification_cost = capex_data.get("certification_cost", 0.0)
    sys_capex.in_vehicle_properties.vehicle_dict = capex_data.get("vehicle_dict", {})
    
    print(f"Purchase Price: €{sys_capex.in_vehicle_properties.purchase_cost:,.2f}")
    print(f"New Vehicle: {sys_capex.in_vehicle_properties.is_new}")
    
    # -------------------- INFRASTRUCTURE --------------------
    sys_capex.in_vehicle_properties.n_slow = capex_data.get("n_slow")
    sys_capex.in_vehicle_properties.n_fast = capex_data.get("n_fast")
    sys_capex.in_vehicle_properties.n_ultra = capex_data.get("n_ultra")
    sys_capex.in_vehicle_properties.n_stations = capex_data.get("n_stations", 0)
    sys_capex.in_vehicle_properties.smart_charging_enabled = capex_data.get("smart_charging_enabled", False)
    
    # -------------------- FINANCING --------------------
    sys_capex.in_vehicle_properties.loan_years = capex_data.get("loan_years", 10)
    
    print(f"Loan Period: {sys_capex.in_vehicle_properties.loan_years} years")
    
    # Run calculation
    sys_capex.add_driver(RunOnce("run_capex"))
    sys_capex.run_drivers()
    
    # Print detailed results
    print("\n" + "-"*80)
    print("CAPEX BREAKDOWN")
    print("-"*80)
    print(f"Vehicle Cost:            €{sys_capex.c_vehicle_cost:>15,.2f}")
    print(f"Infrastructure Cost:     €{sys_capex.c_infrastructure_cost:>15,.2f}")
    print(f"  - Hardware:            €{sys_capex.c_infrastructure_hardware:>15,.2f}")
    print(f"  - Grid Connection:     €{sys_capex.c_infrastructure_grid:>15,.2f}")
    print(f"  - Installation:        €{sys_capex.c_infrastructure_installation:>15,.2f}")
    print(f"Registration Taxes:      €{sys_capex.c_taxes:>15,.2f}")
    print(f"Financing Cost:          €{sys_capex.c_financing_cost:>15,.2f}")
    print(f"Subsidies:              -€{sys_capex.c_subsidies:>15,.2f}")
    print("-"*80)
    print(f"Total CAPEX:             €{sys_capex.c_capex_total:>15,.2f}")
    print(f"Capital Recovery Factor: {sys_capex.c_crf:>16.4f}")
    print(f"CAPEX:    €{sys_capex.c_capex_total:>15,.2f}")
    print("="*80)
    
    return sys_capex.c_capex_total 


def run_opex_truck(opex_inputs: dict) -> float:
    """
    Run OPEX calculation for trucks.
    
    Args:
        opex_inputs: Dictionary with OPEX parameters for trucks
        
    Returns:
        Annual OPEX total
    """
    print("\n" + "="*80)
    print("RUNNING TRUCK OPEX CALCULATION")
    print("="*80)
    
    sys_opex = TruckOPEXCalculator("opex_truck")
    
    # Assign inputs if they exist as system attributes
    for key, value in opex_inputs.items():
        if hasattr(sys_opex, key):
            setattr(sys_opex, key, value)
    sys_opex.in_vehicle_properties.purchase_cost = opex_inputs["purchase_price"]
    sys_opex.add_driver(RunOnce("run_truck"))
    sys_opex.run_drivers()
    sys_opex.print_results()
    
    return sys_opex.o_opex_total


def run_opex_ship(opex_inputs: dict) -> float:
    print("\n" + "="*80)
    print("RUNNING SHIP OPEX CALCULATION")
    print("="*80)
    
    sys_ship = ShipOPEXCalculator("ship_opex_case")
    vp = sys_ship.in_vehicle_properties
    
    # --- CONSOLIDATED & TYPE-SAFE MAPPING ---
    # 1. Mandatory Floats (Must use float() to avoid TypeError)
    vp.purchase_cost = float(opex_inputs.get("purchase_price", 0.0))
    vp.GT = float(opex_inputs.get("GT", 0.0))
    vp.annual_energy_consumption_kWh = float(opex_inputs.get("consumption_energy", 0.0))
    vp.fuel_mass_kg = float(opex_inputs.get("fuel_mass_kg", 0.0))
    
    # 2. Mandatory Strings
    vp.ship_class = str(opex_inputs.get("size_vehicle", "large")) 
    vp.registration_country = str(opex_inputs.get("registration_country", "France"))
    vp.country_oper = str(opex_inputs.get("registration_country", "France"))
    vp.type_energy = str(opex_inputs.get("type_energy", "DIESEL"))
    
    # 3. List Structures
    # Ensure team_size is an int (CosApp lists usually expect specific types)
    crew_size = int(opex_inputs.get("crew_count", 0))
    vp.crew_list = [{"rank": "seafarer", "team_size": crew_size}]
    
    # --- EXECUTION ---
    sys_ship.add_driver(RunOnce("run_ship"))
    sys_ship.run_drivers()
    
    # --- RESULTS DISPLAY ---
    print("\n" + "-"*80)
    print("SHIP OPEX BREAKDOWN")
    print("-"*80)
    print(f"Taxes:           €{sys_ship.o_taxes:>15,.2f}")
    print(f"Port Fees:       €{sys_ship.o_ports:>15,.2f}")
    print(f"Insurance:       €{sys_ship.o_insurance:>15,.2f}")
    print(f"Crew:            €{sys_ship.o_crew:>15,.2f}")
    print(f"Maintenance:     €{sys_ship.o_maintenance:>15,.2f}")
    print(f"Energy:          €{sys_ship.o_energy:>15,.2f}")
    print("-"*80)
    print(f"OPEX Total:      €{sys_ship.o_opex_total:>15,.2f}")
    print("="*80)
    
    return float(sys_ship.o_opex_total)


def run_rv(rv_inputs: dict) -> float:
    """
    Run Residual Value calculation.
    
    Args:
        rv_inputs: Dictionary with RV parameters
        
    Returns:
        Residual value
    """
    print("\n" + "="*80)
    print("RUNNING RESIDUAL VALUE CALCULATION")
    print("="*80)
    
    rv_sys = ResidualValueCalculator("rv_global", type_vehicle=rv_inputs["type_vehicle"])
    
    # Vehicle properties
    rv_sys.in_vehicle_properties.type_vehicle = rv_inputs["type_vehicle"]
    rv_sys.in_vehicle_properties.type_energy = rv_inputs["type_energy"]
    rv_sys.in_vehicle_properties.registration_country = rv_inputs["registration_country"]
    rv_sys.in_vehicle_properties.purchase_cost = rv_inputs["purchase_cost"]
    rv_sys.in_vehicle_properties.year_purchase = rv_inputs["year_purchase"]
    rv_sys.in_vehicle_properties.current_year = rv_inputs["current_year"]
    rv_sys.in_vehicle_properties.travel_measure = rv_inputs["travel_measure"]
    rv_sys.in_vehicle_properties.maintenance_cost = rv_inputs["maintenance_cost"]
    rv_sys.in_vehicle_properties.minimum_fuel_consumption = rv_inputs["minimum_fuel_consumption"]
    rv_sys.in_vehicle_properties.powertrain_model_year = rv_inputs["powertrain_model_year"]
    rv_sys.in_vehicle_properties.warranty = rv_inputs["warranty"]
    rv_sys.in_vehicle_properties.type_warranty = rv_inputs["type_warranty"]
    
    print(f"Vehicle Type: {rv_inputs['type_vehicle']}")
    print(f"Energy Type: {rv_inputs['type_energy']}")
    print(f"Purchase Year: {rv_inputs['year_purchase']}")
    print(f"Current Year: {rv_inputs['current_year']}")
    print(f"Purchase Cost: €{rv_inputs['purchase_cost']:,.2f}")
    
    # Country properties
    rv_sys.in_country_properties.energy_price = rv_inputs["energy_price"]
    rv_sys.in_country_properties.c02_taxes = rv_inputs["co2_taxes"]
    rv_sys.in_country_properties.subsidies = rv_inputs["subsidies"]
    
    rv_sys.add_driver(RunOnce('run_rv'))
    rv_sys.run_drivers()
    
    print("\n" + "-"*80)
    print("RESIDUAL VALUE BREAKDOWN")
    print("-"*80)
    print(f"Total Depreciation:      €{rv_sys.total_depreciation:>15,.2f}")
    print(f"Impact Health Penalties: €{rv_sys.total_impact_health:>15,.2f}")
    print(f"External Factors Adj:    €{rv_sys.total_external_factors:>15,.2f}")
    print("-"*80)
    print(f"FINAL RESIDUAL VALUE:    €{rv_sys.rv:>15,.2f}")
    print("="*80)
    
    return rv_sys.rv


# ======================================================================
# GLOBAL FUNCTION: RUN_TCO_SCENARIO
# ======================================================================

def run_tco_scenario(user_inputs: dict):
    """
    Run complete TCO scenario including CAPEX, OPEX, and RV.
    
    TCO Formula:
    TCO = (CAPEX - RV/(1+r)^N) * CRF + Σ(OPEX_n / (1+r)^n) for n=1 to N
    
    Where:
    - CAPEX: Total capital expenditure
    - RV: Residual value at end of period
    - r: Interest/discount rate
    - N: Number of years
    - CRF: Capital Recovery Factor
    - OPEX_n: Operating expenditure in year n
    
    Args:
        user_inputs: Dictionary containing all scenario parameters
        
    Returns:
        Dictionary with TCO results
    """
    asset_type = user_inputs["asset_type"]
    
    print("\n" + "="*80)
    print(f"TCO SCENARIO: {user_inputs.get('description', 'No description')}")
    print("="*80)
    print(f"Asset Type: {asset_type.upper()}")
    print(f"Powertrain: {user_inputs['powertrain_type']}")
    print(f"Country: {user_inputs['country']}")
    print(f"Operation Period: {user_inputs['operation_years']} years")
    print("="*80)
    
    # 1) CAPEX
    capex_inputs = dict(user_inputs)
    capex_total = run_capex(capex_inputs, asset_type)
    
    # 2) OPEX
    if asset_type == "truck":
        opex_annual = run_opex_truck(user_inputs["opex_truck"])
    elif asset_type == "ship":
        opex_annual = run_opex_ship(user_inputs["opex_ship"])
    else:
        raise ValueError(f"Unknown asset_type: {asset_type}")
    
    # 3) Residual Value
    rv_value = run_rv(user_inputs["rv"])
    
    # 4) Get parameters for TCO calculation
    N = user_inputs["operation_years"]
    interest_rate = user_inputs.get("discount_rate", 0.04)  #
    
    # Get CAPEX total (not annualized) and CRF
    # We need to recalculate to get the total CAPEX before CRF application
    capex_inputs_recalc = dict(user_inputs)
    sys_capex_temp = VehicleCAPEXCalculator("capex_temp", vehicle_type=asset_type)
    
    # Set all properties (simplified - in production you'd use the full setup)
    capex_data = capex_inputs_recalc.get("capex", {})
    sys_capex_temp.in_vehicle_properties.type_vehicle = capex_data.get("powertrain_type", "DIESEL")
    sys_capex_temp.in_vehicle_properties.type_energy = capex_data.get("powertrain_type", "DIESEL")
    sys_capex_temp.in_vehicle_properties.vehicle_number = capex_data.get("vehicle_number", 1)
    sys_capex_temp.in_vehicle_properties.vehicle_id = capex_data.get("vehicle_id", 1)
    sys_capex_temp.in_vehicle_properties.vehicle_weight_class = capex_data.get("vehicle_weight_class", "light")
    sys_capex_temp.in_vehicle_properties.registration_country = capex_data.get("country", "France")
    sys_capex_temp.in_vehicle_properties.year = capex_data.get("year", 2025)
    sys_capex_temp.in_vehicle_properties.is_new = capex_data.get("is_new", True)
    sys_capex_temp.in_vehicle_properties.owns_vehicle = capex_data.get("owns_vehicle", False)
    sys_capex_temp.in_vehicle_properties.purchase_cost = capex_data.get("purchase_price", 0.0)
    sys_capex_temp.in_vehicle_properties.conversion_cost = capex_data.get("conversion_cost", 0.0)
    sys_capex_temp.in_vehicle_properties.certification_cost = capex_data.get("certification_cost", 0.0)
    sys_capex_temp.in_vehicle_properties.vehicle_dict = capex_data.get("vehicle_dict", {})
    sys_capex_temp.in_vehicle_properties.n_slow = capex_data.get("n_slow")
    sys_capex_temp.in_vehicle_properties.n_fast = capex_data.get("n_fast")
    sys_capex_temp.in_vehicle_properties.n_ultra = capex_data.get("n_ultra")
    sys_capex_temp.in_vehicle_properties.n_stations = capex_data.get("n_stations", 0)
    sys_capex_temp.in_vehicle_properties.smart_charging_enabled = capex_data.get("smart_charging_enabled", False)
    sys_capex_temp.in_vehicle_properties.loan_years = capex_data.get("loan_years", 10)
    
    sys_capex_temp.add_driver(RunOnce("run_capex_temp"))
    sys_capex_temp.run_drivers()
    
    capex_total = sys_capex_temp.c_capex_total
    crf = sys_capex_temp.c_crf
    
    # 5) Calculate TCO using the formula:
    # TCO = (CAPEX - RV/(1+r)^N) * CRF + Σ(OPEX / (1+r)^n) for n=1 to N
    
    # Discounted residual value
    rv_discounted = rv_value / ((1 + interest_rate) ** N)
    
    # CAPEX component
    capex_component = (capex_total - rv_discounted) * crf
    
    # OPEX component - Present value of annuity
    opex_component = 0.0
    opex_pv_details = []
    for n in range(1, N + 1):
        opex_pv_year = opex_annual / ((1 + interest_rate) ** n)
        opex_component += opex_pv_year
        opex_pv_details.append((n, opex_pv_year))
    
    # Total TCO
    tco_total = capex_component + opex_component
    
    # Print final summary
    print("\n" + "="*80)
    print("TOTAL COST OF OWNERSHIP (TCO) CALCULATION")
    print("="*80)
    print(f"Discount Rate:           {interest_rate*100:>15.2f}%")
    print(f"Operation Horizon:       {N:>16} years")
    print(f"Capital Recovery Factor: {crf:>16.4f}")
    print("="*80)
    
    print("\nCAPEX COMPONENT:")
    print(f"  Total CAPEX:           €{capex_total:>15,.2f}")
    print(f"  Residual Value:        €{rv_value:>15,.2f}")
    print(f"  RV Discounted (PV):    €{rv_discounted:>15,.2f}")
    print(f"  Net CAPEX:             €{capex_total - rv_discounted:>15,.2f}")
    print(f"  CAPEX Component:       €{capex_component:>15,.2f}")
    
    print("\nOPEX COMPONENT:")
    print(f"  Annual OPEX:           €{opex_annual:>15,.2f}")
    print(f"  Present Value of OPEX stream:")
    for year, pv in opex_pv_details[:5]:  # Show first 5 years
        print(f"    Year {year:2d}:            €{pv:>15,.2f}")
    if N > 5:
        print(f"    ... (years 6-{N})")
    print(f"  Total OPEX (PV):       €{opex_component:>15,.2f}")
    
    print("\n" + "="*80)
    print("TCO SUMMARY")
    print("="*80)
    print(f"CAPEX Component:         €{capex_component:>15,.2f}")
    print(f"OPEX Component (PV):     €{opex_component:>15,.2f}")
    print("-"*80)
    print(f"TOTAL TCO (PV):          €{tco_total:>15,.2f}")
    print(f"Equivalent Annual Cost:  €{tco_total/N:>15,.2f}")
    print(f"tco per distance unit:   €{tco_total/(N*user_inputs.get('annual_distance_travel',80000)):>15,.4f} per unit")

    print("="*80)
    
    return {
        "capex_total": capex_total,
        "capex_component": capex_component,
        "opex_annual": opex_annual,
        "opex_component_pv": opex_component,
        "rv": rv_value,
        "rv_discounted": rv_discounted,
        "tco_total": tco_total,
        "equivalent_annual_cost": tco_total / N,
        "operation_years": N,
        "discount_rate": interest_rate,
        "crf": crf
    }


# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " "*20 + "TCO CALCULATION SYSTEM" + " "*37 + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    
    # Run single scenario - Choose one: "truck" or "ship"
    # Uncomment the scenario you want to run:
    
    # TRUCK SCENARIO
    scenario_inputs_truck_elec = make_example_truck_electric_fleet()
    scenario_inputs_truck_diesel = make_example_truck_diesel()
    scenario_inputs_ship_elec = make_example_ship_electric()
    scenario_inputs_ship_diesel = make_example_ship_diesel()
    
   
    # Run TCO calculation
    results = run_tco_scenario(scenario_inputs_truck_elec)
    #results = run_tco_scenario(scenario_inputs_truck_diesel)
    #results = run_tco_scenario(scenario_inputs_ship_elec)       
    #results = run_tco_scenario(scenario_inputs_ship_diesel)
    
    print("\n" + "#"*80)
    print("# TCO CALCULATION COMPLETED")
    print("#"*80)