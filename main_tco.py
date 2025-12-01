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

# === AJUSTA ESTOS IMPORTS A TUS NOMBRES REALES DE ARCHIVO ===
from capex_calculator import CAPEXSystem
from Opex_Calculator_CosApp import TruckOPEXCalculator
from Opex_Calculator_ships import ShipOPEXCalculator
from rv_functions import ResidualValueCalculator

# ----------------------------------------------------------------------
# 1. ESTRUCTURA DE ENTRADA GENERAL
# ----------------------------------------------------------------------
def make_example_truck_inputs():
    """Ejemplo de diccionario de entrada para un TRUCK."""
    return {
        "asset_type": "truck",
        "description": "Heavy diesel N3 in France",

        # Datos comunes
        "powertrain_type": "diesel",      # para CAPEX / RV (ajusta a tu DB)
        "vehicle_weight_class": "heavy",
        "country": "France",
        "year": 2025,
        "operation_years": 5,

        # ---------- CAPEX ----------
        "capex": {
            "purchase_price": 150_000.0,
            "is_new": True,
            "owns_vehicle": False,
            "conversion_cost": 0.0,
            "certification_cost": 0.0,
            "vehicle_number": 1,
            # energía de flota (ejemplo simple, 1 vehículo)
            "vehicle_dict": {
                1: {"E_t": 42_000.0, "S_t": 0.3, "F_t": 0.5, "U_t": 0.2, "Public_t": 0.0}
            },
            "id": 1,
            "n_slow": None,
            "n_fast": None,
            "n_ultra": None,
            "n_stations": None,
            "smart_charging_enabled": False,
        },

        # ---------- OPEX TRUCK ----------
        "opex_truck": {
            "purchase_cost": 150_000.0,
            "type_energy": "diesel",
            "size_vehicle": "N3",
            "registration_country": "France",
            "annual_distance_travel": 120_000.0,
            "departure_city": "Paris",
            "arrival_city": "Marseille",
            "RV": 45_000.0,
            "N_years": 5.0,
            "team_count": 1,
            "maintenance_cost": 7_000.0,
            "consumption_energy": 42_000.0,
            "fuel_multiplier": 1.0,
            "EF_CO2_diesel": 2.65,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "truck",
            "type_energy": "diesel",
            "registration_country": "France",
            "purchase_cost": 150_000.0,
            "year_purchase": 2020,
            "current_year": 2025,
            "travel_measure": 600_000.0,
            "maintenance_cost": 7_000.0,
            "minimum_fuel_consumption": 250.0,
            "powertrain_model_year" : 2020,
            "warranty" : 5.0,
            "type_warranty" : 'years',

            "energy_price": 1.5,
            "c02_taxes": 500,
            "subsidies":0,
            "vehicle_number": 1,
        },
    }


def make_example_ship_inputs():
    """Ejemplo de diccionario de entrada para un SHIP."""
    return {
        "asset_type": "ship",
        "description": "Cargo ship diesel in Spain",

        # Datos comunes
        "powertrain_type": "diesel",
        "vehicle_weight_class": "heavy",   # puedes inventar una clase “heavy_ship”
        "country": "Spain",
        "year": 2025,
        "operation_years": 5,

        # ---------- CAPEX (aún usando CAPEXSystem genérico) ----------
        "capex": {
            "purchase_price": 12_000_000.0,
            "is_new": True,
            "owns_vehicle": False,
            "conversion_cost": 0.0,
            "certification_cost": 0.0,
            "vehicle_number": 1,
            "vehicle_dict": {
                1: {"E_t": 5_000_000.0, "S_t": 0.0, "F_t": 0.0, "U_t": 0.0, "Public_t": 0.0}
            },
            "id": 1,
            "n_slow": None,
            "n_fast": None,
            "n_ultra": None,
            "n_stations": None,
            "smart_charging_enabled": False,
        },

        # ---------- OPEX SHIP ----------
        "opex_ship": {
            "country_reg": "Spain",
            "country_oper": "Spain",
            "ship_class": "cargo",
            "length": 120.0,
            "energy_type": "diesel",
            "purchase_cost": 12_000_000.0,
            "safety_class": "A",
            "annual_distance": 20_000.0,
            "n_trips_per_year": 10.0,
            "days_per_trip": 4.0,
            "planning_horizon_years": 1.0,
            "maintenance_cost_annual": 150_000.0,
            "crew_list": [
                {"rank": "captain", "attribute": "ferry", "team_size": 1},
                {"rank": "crew", "attribute": "ferry", "team_size": 8},
            ],
            "I_energy": 0.5,
            "EF_CO2": 0.27,
            "NOxSOx_rate": 0.01,
            "annual_energy_consumption_kWh": 5_000_000.0,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "Ship",
            "type_energy": "Diesel_fosile",
            "taxes": 50_000.0,
            "purchase_cost": 12_000_000.0,
            "age_vehicle": 10.0,
            "travel_measure": 200_000.0,  # horas o millas equivalentes
            "maintenance_cost": 500_000.0,
        },
    }


# ----------------------------------------------------------------------
# 2. WRAPPERS PARA CADA MÓDULO
# ----------------------------------------------------------------------
def run_capex(capex_inputs: dict) -> float:
    """Lanza CAPEXSystem y devuelve capex_per_vehicle."""
    sys_capex = CAPEXSystem("capex_global")

    # inputs principales
    sys_capex.powertrain_type = capex_inputs.get("powertrain_type", "bet")
    sys_capex.vehicle_number = capex_inputs.get("vehicle_number", 1)
    sys_capex.id = capex_inputs.get("id", 1)
    sys_capex.vehicle_weight_class = capex_inputs.get("vehicle_weight_class", "heavy")
    sys_capex.country = capex_inputs.get("country", "EU")
    sys_capex.year = capex_inputs.get("year", 2025)

    # vehicle
    sys_capex.is_new = capex_inputs.get("is_new", True)
    sys_capex.owns_vehicle = capex_inputs.get("owns_vehicle", False)
    sys_capex.purchase_price = capex_inputs.get("purchase_price", 0.0)
    sys_capex.conversion_cost = capex_inputs.get("conversion_cost", 0.0)
    sys_capex.certification_cost = capex_inputs.get("certification_cost", 0.0)

    # energía / infraestructura
    sys_capex.vehicle_dict = capex_inputs.get("vehicle_dict", {})
    sys_capex.n_slow = capex_inputs.get("n_slow")
    sys_capex.n_fast = capex_inputs.get("n_fast")
    sys_capex.n_ultra = capex_inputs.get("n_ultra")
    sys_capex.n_stations = capex_inputs.get("n_stations")
    sys_capex.smart_charging_enabled = capex_inputs.get("smart_charging_enabled", False)

    driver = sys_capex.add_driver(RunOnce("run_capex"))
    sys_capex.run_drivers()

    return sys_capex.capex_per_vehicle


def run_opex_truck(opex_inputs: dict) -> float:
    """Lanza TruckOPEXCalculator y devuelve o_opex_total."""
    sys_opex = TruckOPEXCalculator("opex_truck", db_path="data_opex_trucks.json")

    # copiar todas las claves que existan
    for key, value in opex_inputs.items():
        if hasattr(sys_opex, key):
            setattr(sys_opex, key, value)

    sys_opex.print_input_summary()
    driver = sys_opex.add_driver(RunOnce("run_truck"))
    sys_opex.run_drivers()
    sys_opex.print_results()

    return sys_opex.o_opex_total


def run_opex_ship(opex_inputs: dict) -> float:
    """Lanza ShipOPEXCalculator y devuelve o_opex_total."""
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
    """Lanza ResidualValueCalculator y devuelve residual_value."""
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
    rv_sys.add_driver(RunOnce('run1'))

    # Run the system
    rv_sys.run_drivers()

    print("\n--- RV RESULTS ---")
    print("\n" + "-"*80)
    print("DEPRECIATION")
    print("-"*80)
    print(f"Total Depreciation Value: ${rv_sys.total_depreciation:,.2f}")
    
    print("\n" + "-"*80)
    print("IMPACT HEALTH PENALTIES")
    print("-"*80)
    print(f"  Total Impact Health:      ${rv_sys.total_impact_health:,.2f}")
    
    print("\n" + "-"*80)
    print("EXTERNAL FACTORS")
    print("-"*80)
    print(f"External Factors Adjustment: ${rv_sys.total_external_factors:,.2f}")
    
    print("\n" + "="*80)
    print(f"FINAL RESIDUAL VALUE: ${rv_sys.rv:,.2f}")
    print("="*80)

    return rv_sys.rv


# ----------------------------------------------------------------------
# 3. FUNCIÓN GLOBAL: RUN_TCO_SCENARIO
# ----------------------------------------------------------------------
def run_tco_scenario(user_inputs: dict):
    """
    Orquesta CAPEX + OPEX + RV para un escenario dado.
    user_inputs viene de make_example_truck_inputs() o make_example_ship_inputs().
    """
    asset_type = user_inputs["asset_type"]
    print("\n" + "=" * 80)
    print(f"RUNNING GLOBAL TCO SCENARIO: {user_inputs.get('description', '')}")
    print("=" * 80)
    print(f"Asset type: {asset_type}")

    # 1) CAPEX
    capex_inputs = dict(user_inputs["capex"])
    # añadimos cosas comunes que capex necesita
    capex_inputs["powertrain_type"] = user_inputs["powertrain_type"]
    capex_inputs["vehicle_weight_class"] = user_inputs["vehicle_weight_class"]
    capex_inputs["country"] = user_inputs["country"]
    capex_inputs["year"] = user_inputs["year"]

    capex_per_year = run_capex(capex_inputs)
    print(f"\n[CAPEX] CAPEX anualizado por vehículo (CRF aplicado): {capex_per_year:,.2f} €")

    # 2) OPEX
    if asset_type == "truck":
        opex_total = run_opex_truck(user_inputs["opex_truck"])
    elif asset_type == "ship":
        opex_total = run_opex_ship(user_inputs["opex_ship"])
    else:
        raise ValueError(f"asset_type desconocido: {asset_type}")
    print(f"[OPEX] OPEX anual total: {opex_total:,.2f} €")

    # 3) RV
    rv_value = run_rv(user_inputs["rv"])
    print(f"[RV] Residual value al final del horizonte: {rv_value:,.2f} €")

    # 4) Ejemplo de TCO (muy simple, puedes cambiar la fórmula)
    N = user_inputs["operation_years"]
    tco = capex_per_year * N + opex_total * N - rv_value

    print("\n" + "=" * 80)
    print("RESUMEN TCO (ejemplo simple)")
    print("=" * 80)
    print(f"Horizonte: {N} años")
    print(f"CAPEX acumulado: {capex_per_year * N:,.2f} €")
    print(f"OPEX acumulado: {opex_total * N:,.2f} €")
    print(f"Residual Value restado: {rv_value:,.2f} €")
    print("-" * 80)
    print(f"TCO total aproximado: {tco:,.2f} €")
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
