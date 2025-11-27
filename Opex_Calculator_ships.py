"""
CosApp System for calculating ship OPEX costs using external data base and json outputs

===============================================================================
COLOR CODING FROM DIAGRAMS:
===============================================================================

[YELLOW] ARROWS = DATABASE PARAMETERS (Retrieved automatically)
   - National/regional standards and rates (taxes, insurance, wages, energy)
   

[ORANGE] ARROWS = USER INPUTS + DIGITAL TWIN OUTPUTS (Must be provided)
   - User Inputs: ship characteristics, crew, distance, etc.
   - Digital Twin: energy consumption, EF_CO2, NOx/SOx, etc.

[GREEN] ARROWS = SYSTEM OUTPUTS (Calculated results)
   - O_Taxes_ship, O_Ports_ship, O_Insurance_ship, O_Crew_ship,
     O_Energy_ship, O_Maintenance_ship, O_OPEX_ship_Total
"""

import json
import sys

from cosapp.drivers import RunOnce 

from cosapp.base import System
from cosapp.ports import Port


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# 0. SHIPS TYPES
# ============================================================================
SHIP_CLASS_TO_TRUCK_CLASS = {
   
    "fishing": "N1",
    "small": "N1",
    "crew_transport": "N1",

    "ferry": "N2",
    "medium": "N2",

    "cargo": "N3",
    "container": "N3",
    "large": "N3",
}


# ============================================================================
# 1. PORTS DE SHIPS (ORANGE + GREEN)
# ============================================================================

class ShipOPEXPort(Port): #“conector” de variables (entrada/salida agrupadas).
    """Port for OPEX calculation inputs and outputs for ships."""

    def setup(self):
        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_variable("country_reg", dtype=str, desc="Country of registration")
        self.add_variable("country_oper", dtype=str, desc="Country of operation")

        self.add_variable("ship_class", dtype=str, desc="Ship class (cargo, ferry, fishing...)")
        self.add_variable("length", dtype=float, desc="Ship length in meters")
        self.add_variable("energy_type", dtype=str, desc="Type of energy (diesel, electric...)")
        self.add_variable("purchase_cost", dtype=float, desc="Purchase cost in EUR")
        self.add_variable("safety_class", dtype=str, desc="Safety class")
        self.add_variable("annual_distance", dtype=float, desc="Annual distance travelled (km or nm)")

        # Ports / trips
        self.add_variable("n_trips_per_year", dtype=float, desc="Number of trips per year")
        self.add_variable("days_per_trip", dtype=float, desc="Number of days per trip")

        # Crew
        self.add_variable("planning_horizon_years", dtype=float, desc="Number of years N")
        self.add_variable("maintenance_cost_annual", dtype=float, desc="Annual maintenance cost in EUR")

        # -------------------- DIGITAL TWIN / USER ENV (ORANGE) --------------------
        self.add_variable("I_energy", dtype=float, desc="Energy consumption per km (MWh/km or ton/km)")
        self.add_variable(
            "EF_CO2",
            dtype=float,
            desc="CO2 emission factor per unit of energy (kg CO2 / kWh or per ton)"
        )
        self.add_variable(
            "NOxSOx_rate",
            dtype=float,
            desc="NOx/SOx emission per km (kg/km)"
        )

        self.add_variable(
            "annual_energy_consumption_kWh",
            dtype=float,
            desc="Annual energy consumption retrieved from digital twin (kWh)"
        )

        # -------------------- OUTPUTS (GREEN) --------------------
        self.add_variable("o_taxes", dtype=float, desc="Total annual taxes for ship in EUR")
        self.add_variable("o_ports", dtype=float, desc="Total annual ports costs in EUR")
        self.add_variable("o_insurance", dtype=float, desc="Total annual insurance in EUR")
        self.add_variable("o_crew", dtype=float, desc="Total crew cost in EUR")
        self.add_variable("o_maintenance", dtype=float, desc="Annual maintenance in EUR")
        self.add_variable("o_energy", dtype=float, desc="Annual energy cost in EUR")
        self.add_variable("o_opex_total", dtype=float, desc="Total OPEX for ship in EUR")


# ============================================================================
# 2. SHIP OPEX COSAPP SYSTEM
# ============================================================================

class ShipOPEXCalculator(System): #modelo OPEX de barcos.
    
    #TEST
    def setup(self, db_path: str = "data_opex_trucks.json"):
        # -------------------- CARGA DE BASE DE DATOS BOAT (YELLOW) --------------------
        with open(db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        # country -> opex_database (taxes, tolls, insurance, crew, energy)
        object.__setattr__(
            self, "_countries_data",
            {c["country"]: c["opex_database"] for c in db_data["countries"]}
        )

        # -------------------- PORT SHIP (ORANGE+GREEN) --------------------
        self.add_inward("opex_ship", ShipOPEXPort, desc="OPEX calculation port for ships")

        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_inward("country_reg", "Spain", dtype=str)
        self.add_inward("country_oper", "Spain", dtype=str)

        self.add_inward("ship_class", "cargo", dtype=str)
        self.add_inward("length", 100.0, dtype=float)
        self.add_inward("energy_type", "diesel", dtype=str)
        self.add_inward("purchase_cost", 10_000_000.0, dtype=float)
        self.add_inward("safety_class", "A", dtype=str)
        self.add_inward("annual_distance", 20_000.0, dtype=float)

        self.add_inward("n_trips_per_year", 10.0, dtype=float)
        self.add_inward("days_per_trip", 5.0, dtype=float)

        self.add_inward("planning_horizon_years", 1.0, dtype=float)
        self.add_inward("maintenance_cost_annual", 100_000.0, dtype=float)

        # Crew list (ORANGE, pero como estructura Python)
        # Ejemplo por defecto: 1 capitán + 5 tripulantes
        self.add_inward(
            "crew_list",
            [
                {"rank": "captain", "attribute": "ferry", "team_size": 1},
                {"rank": "crew",    "attribute": "ferry", "team_size": 8},
            ],
            desc="Lista de diccionarios de crew: rank, attribute, team_size",
        )

        # -------------------- DIGITAL TWIN / USER ENV (ORANGE) --------------------
        self.add_inward("I_energy", 0.5, desc="MWh/km or ton/km")
        self.add_inward("EF_CO2", 0.27, desc="kg CO2 per unit of energy")
        self.add_inward("NOxSOx_rate", 0.01, desc="kg NOx/SOx per km")
        self.add_inward(
            "annual_energy_consumption_kWh",
            5_000_000.0,
            desc="Annual energy consumption from digital twin simulation"
        )

        # -------------------- OUTPUTS (GREEN) --------------------
        self.add_outward("o_taxes", 0.0, desc="Total annual taxes")
        self.add_outward("o_ports", 0.0, desc="Total annual ports costs")
        self.add_outward("o_insurance", 0.0, desc="Total annual insurance")
        self.add_outward("o_crew", 0.0, desc="Total crew cost")
        self.add_outward("o_maintenance", 0.0, desc="Annual maintenance")
        self.add_outward("o_energy", 0.0, desc="Annual energy cost")
        self.add_outward("o_opex_total", 0.0, desc="Total OPEX ships")

    # ==================== DATABASE ACCESS METHODS ====================

    def get_db_params(self, country: str, category: str):
        if country not in self._countries_data:
            raise ValueError(f"Country '{country}' not found in database")
        return self._countries_data[country][category]

    def _map_ship_class_to_truck_class(self, ship_class: str) -> str:
        return SHIP_CLASS_TO_TRUCK_CLASS.get(ship_class, "N3")  # default N3 = big ship
    

# ============================================================================
# 3. SHIP COMPUTE
# ============================================================================

    # ==================== O_TAXES SHIP ====================

    def compute_o_taxes_ship(self):
        """
        O_taxes_ship ≈tax_reg(c,k,L) +tax_annual(c,k,L) + D * (I_energy * tax_energy(c,e)) + D * (I_energy * EF_CO2 * tax_CO2(c,e)) + D * (NOxSOx_rate * tax_NOxSOx(c,k,e)) 
        + B_env(c,k,e)

        Donde:
          - c: country_reg
          - k: ship_class mapeada a N1/N2/N3
          - e: energy_type
          - D: annual_distance
        """
        taxes_db = self.get_db_params(self.country_reg, "taxes")

        #TO COMPARATE
        k_truck = self._map_ship_class_to_truck_class(self.ship_class)

        tax_reg = taxes_db["tax_reg_c_k_L"].get(k_truck, 0.0)
        tax_annual = taxes_db["tax_annual_c_k_L"].get(k_truck, 0.0)
        tax_energy = taxes_db["tax_energy_c_e"].get(self.energy_type, 0.0)
        tax_CO2 = taxes_db["tax_CO2_c_e"]
        B_env = taxes_db["B_env_c_k_e"].get(self.energy_type, 0.0)

        # NOxSOx
        tax_NOxSOx = 0.0

        D = self.annual_distance
        I_energy = self.I_energy
        EF_CO2 = self.EF_CO2
        NOxSOx_rate = self.NOxSOx_rate

        energy_tax_component = D * I_energy * tax_energy
        co2_tax_component = D * I_energy * EF_CO2 * tax_CO2
        noxsox_tax_component = D * NOxSOx_rate * tax_NOxSOx

        self.o_taxes = (tax_reg+ tax_annual+ energy_tax_component+ co2_tax_component+ noxsox_tax_component+ B_env)

    # ==================== O_PORTS SHIP ====================

    def compute_o_ports_ship(self):
        """
        O_ports_ship = price_per_day × (n_trips_per_year × days_per_trip)

        """
        price_per_day = 0.0  # to fill from DB
        days_total = self.n_trips_per_year * self.days_per_trip
        self.o_ports = price_per_day * days_total

    # ==================== O_INSURANCE SHIP ====================

    def compute_o_insurance_ship(self):
        """
        O_insurance_ship = insurance_rate(c, e) × (purchase_cost - RV_ship)

        bring RV from RV_ship
        """
        insurance_db = self.get_db_params(self.country_reg, "insurance")

        if self.energy_type not in insurance_db["insurance_rate_c_L_e_safety"]:
            insurance_rate = 0.0
        else:
            insurance_rate = insurance_db["insurance_rate_c_L_e_safety"][self.energy_type]

        RV_ship = 0.0  # RV
        self.o_insurance = insurance_rate * (self.purchase_cost - RV_ship)

    # ==================== O_CREW SHIP ====================

    def compute_o_crew_ship(self):
        """
        O_crew_ship = Σ (wage_rank × team_i) × N_years
        """
        crew_db = self.get_db_params(self.country_reg, "crew")
        wages = crew_db["wage_of_crew_rank"]
        wage_default = wages.get("driver", 30_000.0) #captain

        total_wage_year = 0.0

        for member in self.crew_list:
            rank = member["rank"]
            team_i = member["team_size"]
            wage_rank = wages.get(rank, wage_default)
            total_wage_year += wage_rank * team_i

        self.o_crew = total_wage_year * self.planning_horizon_years

    # ==================== O_MAINTENANCE SHIP ====================

    def compute_o_maintenance_ship(self):
        self.o_maintenance = self.maintenance_cost_annual

    # ==================== O_ENERGY SHIP ====================

    def compute_o_energy_ship(self):
        """
        O_energy_ship = annual_energy_consumption_kWh × energy_price(c_oper, e)
        """
        energy_db = self.get_db_params(self.country_oper, "energy")
        if self.energy_type not in energy_db["energy_price_c_e"]:
            energy_price = 0.0
        else:
            energy_price = energy_db["energy_price_c_e"][self.energy_type]

        self.o_energy = self.annual_energy_consumption_kWh * energy_price

######################### MAIN COMPUTE ###########################################

    def compute(self):
        """
        Main compute method for ships:
          OPEX_ship = O_taxes + O_ports + O_insurance + O_crew + O_maintenance + O_energy
        """
        
        p = self.opex_ship

        # calculate by module
        self.compute_o_taxes_ship()
        self.compute_o_ports_ship()
        self.compute_o_insurance_ship()
        self.compute_o_crew_ship()
        self.compute_o_maintenance_ship()
        self.compute_o_energy_ship()

        # Total OPEX
        self.o_opex_total = (self.o_taxes+ self.o_ports+ self.o_insurance+ self.o_crew+ self.o_maintenance+ self.o_energy)

        # Populate port outputs
        p.country_reg = self.country_reg
        p.country_oper = self.country_oper
        p.ship_class = self.ship_class
        p.length = self.length
        p.energy_type = self.energy_type
        p.purchase_cost = self.purchase_cost
        p.safety_class = self.safety_class
        p.annual_distance = self.annual_distance

        p.n_trips_per_year = self.n_trips_per_year
        p.days_per_trip = self.days_per_trip

        p.planning_horizon_years = self.planning_horizon_years
        p.maintenance_cost_annual = self.maintenance_cost_annual

        p.I_energy = self.I_energy
        p.EF_CO2 = self.EF_CO2
        p.NOxSOx_rate = self.NOxSOx_rate
        p.annual_energy_consumption_kWh = self.annual_energy_consumption_kWh

        p.o_taxes = self.o_taxes
        p.o_ports = self.o_ports
        p.o_insurance = self.o_insurance
        p.o_crew = self.o_crew
        p.o_maintenance = self.o_maintenance
        p.o_energy = self.o_energy
        p.o_opex_total = self.o_opex_total

    # ==================== SAVE DATA IN JSON FILE ====================

    def save_results_to_json(self, filename: str = "resultado_opex_ship.json"):
        """Save results from ships"""
        data_out = {
            "country_reg": self.country_reg,
            "country_oper": self.country_oper,
            "ship_class": self.ship_class,
            "length": self.length,
            "energy_type": self.energy_type,
            "purchase_cost": self.purchase_cost,
            "safety_class": self.safety_class,
            "annual_distance": self.annual_distance,
            "n_trips_per_year": self.n_trips_per_year,
            "days_per_trip": self.days_per_trip,
            "planning_horizon_years": self.planning_horizon_years,
            "maintenance_cost_annual": self.maintenance_cost_annual,
            "crew_list": self.crew_list,
            "I_energy": self.I_energy,
            "EF_CO2": self.EF_CO2,
            "NOxSOx_rate": self.NOxSOx_rate,
            "annual_energy_consumption_kWh": self.annual_energy_consumption_kWh,
            "o_taxes": self.o_taxes,
            "o_ports": self.o_ports,
            "o_insurance": self.o_insurance,
            "o_crew": self.o_crew,
            "o_maintenance": self.o_maintenance,
            "o_energy": self.o_energy,
            "o_opex_total": self.o_opex_total,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_out, f, indent=4, ensure_ascii=False)

        print(f"\nShip OPEX results saved to: {filename}")



    #============================= SCENARIOS INPUTS=====================

def run_ship_scenario(
    scenario_name: str,
    inputs_path: str = "inputs_ship.json",
    db_path: str = "data_opex_trucks.json",
):
    print("\n" + "#" * 80)
    print(f"### RUNNING SHIP SCENARIO: {scenario_name} ###")
    print("#" * 80)

    # Rutas absolutas
    inputs_full_path = os.path.join(BASE_DIR, inputs_path)
    db_full_path = os.path.join(BASE_DIR, db_path)

    # 1. Cargar todos los escenarios
    with open(inputs_full_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    scenarios = all_data.get("scenarios", [])

    # 2. Buscar el escenario por name
    scenario = None
    for sc in scenarios:
        if sc.get("name") == scenario_name:
            scenario = sc
            break

    if scenario is None:
        raise ValueError(f"Scenario '{scenario_name}' not found in {inputs_full_path}")

    # 3. Crear sistema CosApp
    sys_ship = ShipOPEXCalculator("ship_opex_case", db_path=db_full_path)

    # 4. Asignar inputs dinámicamente con casteo de tipos
    for key, value in scenario.items():
        if key in ("name", "description"):
            continue
        if not hasattr(sys_ship, key):
            continue

        current = getattr(sys_ship, key)
        try:
            if isinstance(current, (float, int)) and isinstance(value, (int, float)):
                value = type(current)(value)
            elif isinstance(current, str):
                value = str(value)
        except Exception:
            pass

        setattr(sys_ship, key, value)

    # 5. Ejecutar
    driver = sys_ship.add_driver(RunOnce("run"))
    sys_ship.run_drivers()

    # 6. Imprimir resultados
    print("\n--- SHIP OPEX RESULTS ---")
    print(f"O_taxes:       {sys_ship.o_taxes:.2f} €")
    print(f"O_ports:       {sys_ship.o_ports:.2f} €")
    print(f"O_insurance:   {sys_ship.o_insurance:.2f} €")
    print(f"O_crew:        {sys_ship.o_crew:.2f} €")
    print(f"O_maintenance: {sys_ship.o_maintenance:.2f} €")
    print(f"O_energy:      {sys_ship.o_energy:.2f} €")
    print(f"OPEX_total:    {sys_ship.o_opex_total:.2f} €")

    # 7. Guardar resultados en JSON específico del escenario
    safe_name = scenario_name.replace(" ", "_")
    out_json = os.path.join(BASE_DIR, f"resultado_opex_ship_{safe_name}.json")
    sys_ship.save_results_to_json(out_json)
    print(f"Resultados guardados en: {out_json}")

    return sys_ship

# ============================================================================
# 4. SHIP MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CosApp Ships OPEX Calculator - Run Scenarios")
    print("=" * 80)

    #Chose quelque scenario
    #run_ship_scenario("scenario1_cargo_diesel_france")
    run_ship_scenario("scenario2_ferry_diesel_spain")
    #run_ship_scenario("scenario3_ferry_electric_germany")
    #run_ship_scenario("scenario4_fishing_diesel_italy")

    print("\n\n========================================")
