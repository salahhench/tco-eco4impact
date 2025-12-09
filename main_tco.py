"""
Main TCO orchestrator for Eco4Impact / BoatTwin project.

- Llama a:
    * CAPEXSystem   (capex_calculator.py)
    * TruckOPEXCalculator (Opex_Calculator_CosApp.py)
    * ShipOPEXCalculator  (Opex_Calculator_ships.py)
    * ResidualValueSystem (rv_calculator.py, por ejemplo)

- Usa una ENTRADA GENERAL (user_inputs) con:
    asset_type: "truck" o "ship"
    powertrain_type, country, etc.

- Calcula y muestra:
    CAPEX, OPEX, RV y un ejemplo de TCO_total.
"""

from cosapp.drivers import RunOnce


from functions.Opex_Calculator_trucks import TruckOPEXCalculator
from functions.Opex_Calculator_ships import ShipOPEXCalculator
from functions.rv_calculator import ResidualValueCalculator
from functions.capex_calculator import VehicleCAPEXCalculator
from inputs.gen_truck_in import make_example_truck_inputs
from inputs.gen_ship_in import make_example_ship_inputs

# ----------------------------------------------------------------------
# 2. WRAPPERS FOR EACH MODULE
# ----------------------------------------------------------------------
def run_capex(capex_inputs: dict) -> float:
    capex_inputs = capex_inputs.get("capex", {})

    sys_capex = VehicleCAPEXCalculator("capex_global")

    # -------------------- MAIN USER INPUTS --------------------
    sys_capex.powertrain_type      = capex_inputs.get("powertrain_type", "diesel")
    sys_capex.vehicle_number       = capex_inputs.get("vehicle_number", 1)
    sys_capex.vehicle_id           = capex_inputs.get("vehicle_id", 1)
    sys_capex.vehicle_weight_class = capex_inputs.get("vehicle_weight_class", "light")
    sys_capex.country              = capex_inputs.get("country", "FR")
    sys_capex.year                 = capex_inputs.get("year", 2025)

    # -------------------- VEHICLE ACQUISITION --------------------
    sys_capex.is_new             = capex_inputs.get("is_new", True)
    sys_capex.owns_vehicle       = capex_inputs.get("owns_vehicle", False)
    sys_capex.purchase_price     = capex_inputs.get("purchase_price", 0.0)
    sys_capex.conversion_cost    = capex_inputs.get("conversion_cost", 0.0)
    sys_capex.certification_cost = capex_inputs.get("certification_cost", 0.0)
    sys_capex.vehicle_dict = capex_inputs.get("vehicle_dict", {})

    # -------------------- INFRASTRUCTURE --------------------
    sys_capex.n_slow                = capex_inputs.get("n_slow")
    sys_capex.n_fast                = capex_inputs.get("n_fast")
    sys_capex.n_ultra               = capex_inputs.get("n_ultra")
    sys_capex.n_stations            = capex_inputs.get("n_stations", 0)
    sys_capex.smart_charging_enabled = capex_inputs.get("smart_charging_enabled", False)

    # -------------------- FINANCING --------------------
    sys_capex.loan_years = capex_inputs.get("loan_years", 10)

    sys_capex.add_driver(RunOnce("run_capex"))
    sys_capex.run_drivers()

    return sys_capex.c_capex_per_vehicle


def run_opex_truck(opex_inputs: dict) -> float:
    
    sys_opex = TruckOPEXCalculator("opex_truck", db_path="data_opex_trucks.json")

    
    for key, value in opex_inputs.items():
        if hasattr(sys_opex, key):
            setattr(sys_opex, key, value)

    sys_opex.print_input_summary()
    sys_opex.add_driver(RunOnce("run_truck"))
    sys_opex.run_drivers()
    sys_opex.print_results()

    return sys_opex.o_opex_total


def run_opex_ship(opex_inputs: dict) -> float:
    
    sys_ship = ShipOPEXCalculator("ship_opex_case", db_path="data_opex_trucks.json")

    for key, value in opex_inputs.items():
        if hasattr(sys_ship, key):
            setattr(sys_ship, key, value)

    driver = sys_ship.add_driver(RunOnce("run_ship"))
    sys_ship.run_drivers()

    print("\n--- SHIP OPEX RESULTS ---")
    print(f"O_taxes:       {sys_ship.o_taxes:.2f} €")
    print(f"O_ports:       {sys_ship.o_ports:.2f} €")
    print(f"O_insurance:   {sys_ship.o_insurance:.2f} €")
    print(f"O_crew:        {sys_ship.o_crew:.2f} €")
    print(f"O_maintenance: {sys_ship.o_maintenance:.2f} €")
    print(f"O_energy:      {sys_ship.o_energy:.2f} €")
    print(f"OPEX_total:    {sys_ship.o_opex_total:.2f} €")

    return sys_ship.o_opex_total


def run_rv(rv_inputs: dict) -> float:
   
    rv_sys = ResidualValueCalculator("rv_global")

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
    
    # Country properties
    rv_sys.in_country_properties.energy_price = rv_inputs["energy_price"]
    rv_sys.in_country_properties.c02_taxes = rv_inputs["co2_taxes"]
    rv_sys.in_country_properties.subsidies = rv_inputs["subsidies"]

    # Run calculation
    rv_sys.add_driver(RunOnce('run_rv'))

    # Run the system
    rv_sys.run_drivers()

    print("\n--- RV RESULTS ---")
    print("\n" + "-"*80)
    print("DEPRECIATION")
    print(f"Total Depreciation Value: ${rv_sys.total_depreciation:,.2f}")
    
    print("\n" + "-"*80)
    print("IMPACT HEALTH PENALTIES")
    print(f"  Total Impact Health: ${rv_sys.total_impact_health:,.2f}")
    
    print("\n" + "-"*80)
    print("EXTERNAL FACTORS")
    print(f"External Factors Adjustment: ${rv_sys.total_external_factors:,.2f}")
    
    print("\n" + "="*80)
    print(f"FINAL RESIDUAL VALUE: ${rv_sys.rv:,.2f}")
    print("="*80)

    return rv_sys.rv


# ----------------------------------------------------------------------
# 3. FUNCIÓN GLOBAL: RUN_TCO_SCENARIO
# ----------------------------------------------------------------------
def run_tco_scenario(user_inputs: dict):
    
    asset_type = user_inputs["asset_type"]
    print("\n" + "=" * 80)
    print(f"RUNNING GLOBAL TCO SCENARIO: {user_inputs.get('description', '')}")
    print("=" * 80)
    print(f"Asset type: {asset_type}")

    # 1) CAPEX
    capex_inputs = dict(user_inputs["capex"])
    
    capex_inputs["powertrain_type"] = user_inputs["powertrain_type"]
    capex_inputs["vehicle_weight_class"] = user_inputs["vehicle_weight_class"]
    capex_inputs["country"] = user_inputs["country"]
    capex_inputs["year"] = user_inputs["year"]

    capex_per_year = run_capex(capex_inputs)
    print(f"\n[CAPEX] CAPEX per vehicle: {capex_per_year:,.2f} €")

    # 2) OPEX
    if asset_type == "truck":
        opex_total = run_opex_truck(user_inputs["opex_truck"])
    elif asset_type == "ship":
        opex_total = run_opex_ship(user_inputs["opex_ship"])
    else:
        raise ValueError(f"asset_type desconocido: {asset_type}")
    print(f"[OPEX] OPEX annual: {opex_total:,.2f} €")

    # 3) RV
    rv_value = run_rv(user_inputs["rv"])
    print(f"[RV]: {rv_value:,.2f} €")

    
    N = user_inputs["operation_years"]
    tco = capex_per_year * N + opex_total * N - rv_value

    print("\n" + "=" * 80)
    print("TCO SUMMARY")
    print("=" * 80)
    print(f"Horizon: {N} años")
    print(f"CAPEX acumulated: {capex_per_year * N:,.2f} €")
    print(f"OPEX acumulated: {opex_total * N:,.2f} €")
    print(f"Residual Value: {rv_value:,.2f} €")
    print("-" * 80)
    print(f"TCO total: {tco:,.2f} €")
    print("=" * 80)

    return {
        "capex_per_year": capex_per_year,
        "opex_per_year": opex_total,
        "rv": rv_value,
        "tco_total": tco,
    }


# ----------------------------------------------------------------------
# 4. MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Escenario TRUCK
    truck_inputs = make_example_truck_inputs()
    run_tco_scenario(truck_inputs)

    # Escenario SHIP
    ship_inputs = make_example_ship_inputs()
    run_tco_scenario(ship_inputs)
