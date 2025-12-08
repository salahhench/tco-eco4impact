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
import os

from cosapp.drivers import RunOnce 
from cosapp.base import System
from cosapp.ports import Port


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


SHIP_CLASS_TO_DB_KEY = {
    "large": "ro_pax_large",
    "big": "ro_pax_large",
    "cargo_large": "ro_pax_large"
}

# INPUTS DIGITAL MODEL

        # annual_energy_consumption_kWh
        #I_energy
        #EF_CO2
        #NOxSOx_rate
        #fuel_mass_g




# ============================================================================
# 1. PORTS DE SHIPS (ORANGE + GREEN)
# ============================================================================

class ShipOPEXPort(Port):  
    """Port for OPEX calculation inputs and outputs for ships."""

    def setup(self):
        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_variable("country_reg", dtype=str, desc="Country of registration")
        self.add_variable("country_oper", dtype=str, desc="Country of operation")

        self.add_variable("ship_class", dtype=str, desc="Ship class key used in DB (ro_pax_small, fishing_large, ctv_medium, ro_pax, small, medium, large, ctv...)")
        self.add_variable("length", dtype=float, desc="Ship length in meters")
        self.add_variable("energy_type", dtype=str, desc="Type of energy (DIESEL, BET, FCET...)")
        self.add_variable("purchase_cost", dtype=float, desc="Purchase cost in EUR")
        self.add_variable("safety_class", dtype=str, desc="Safety class")
        self.add_variable("annual_distance", dtype=float, desc="Annual distance travelled (km or nm)")

        # Gross tonnage (nuevo input)
        self.add_variable("GT", dtype=float, desc="Gross tonnage (GT) of the ship")

        # Ports / trips (pueden no usarse en la nueva fórmula, pero los dejamos por si acaso)
        self.add_variable("n_trips_per_year", dtype=float, desc="Number of trips per year")
        self.add_variable("days_per_trip", dtype=float, desc="Number of days per trip")

        # Crew
        self.add_variable("planning_horizon_years", dtype=float, desc="Number of years N")
        self.add_variable("maintenance_cost_annual", dtype=float, desc="Annual maintenance cost in EUR (legacy)")
        # Opción alternativa: costo mensual total de tripulación si lo quieres dar directo
        self.add_variable("crew_monthly_total", dtype=float, desc="Total monthly crew cost (EUR). If 0, use seafarer * crew size.")

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

        # fuel mass
        self.add_variable(
            "fuel_mass_g",
            dtype=float,
            desc="Fuel mass used in a period (g), provided by digital twin"
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

class ShipOPEXCalculator(System):  
    
    def setup(self, db_path: str = "db_ships.json"):
        # -------------------- DATA BASE SHIPS (YELLOW) --------------------
        with open(db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        # country -> full country dict (taxes_opex / taxes, ports, insurance, crew, energy, maintenance)
        object.__setattr__(
            self, "_countries_data",
            {c["country"]: c for c in db_data["countries"]}
        )

        # -------------------- PORT SHIP (ORANGE+GREEN) --------------------
        self.add_inward("opex_ship", ShipOPEXPort, desc="OPEX calculation port for ships")

        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_inward("country_reg", "France", dtype=str)
        self.add_inward("country_oper", "France", dtype=str)
        self.add_inward("ship_class", "ro_pax_large", dtype=str)

        self.add_inward("length", 100.0, dtype=float)
        self.add_inward("energy_type", "DIESEL", dtype=str)
        self.add_inward("purchase_cost", 10_000_000.0, dtype=float)
        self.add_inward("safety_class", "A", dtype=str)
        self.add_inward("annual_distance", 20_000.0, dtype=float)

        # GT nuevo
        self.add_inward("GT", 0.0, dtype=float)


        self.add_inward("n_trips_per_year", 10.0, dtype=float)
        self.add_inward("days_per_trip", 5.0, dtype=float)

        self.add_inward("planning_horizon_years", 1.0, dtype=float)
        self.add_inward("maintenance_cost_annual", 100_000.0, dtype=float)

        # Costo mensual total opcional de crew
        self.add_inward("crew_monthly_total", 0.0, dtype=float)

        self.add_inward(
            "crew_list",
            [
                {"rank": "seafarer", "attribute": "ro_pax_large", "team_size": 10},
            ],
            desc="CREW: rank, attribute, team_size",
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

        
        self.add_inward("fuel_mass_kg", 0.0, dtype=float)

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
        
        country_db = self._countries_data[country]

        # Soportar "taxes" y "taxes_opex"
        if category == "taxes_opex" or category == "taxes":
            if "taxes_opex" in country_db:
                return country_db["taxes_opex"]
            if "taxes" in country_db:
                return country_db["taxes"]
            raise ValueError(f"No 'taxes_opex' or 'taxes' entry for country '{country}'")
        
        if category in country_db:
            return country_db[category]
        
        raise ValueError(f"Category '{category}' not found for country '{country}'")

    def _map_ship_class_to_db_key(self, ship_class: str) -> str:
        #take possibles values from users inputs
        return SHIP_CLASS_TO_DB_KEY.get(ship_class, ship_class)
        

# ============================================================================
# 3. SHIP COMPUTE
# ============================================================================

    # ==================== O_TAXES SHIP ====================

    def compute_o_taxes_ship(self):
        """

       Use the taxes_opex section of the database.
      Take the energy type from the user input.
      Take the fuel mass (fuel_mass_ton, in ton) provided by the digital twin.
      Look up in tax_energy_c_e the vector of 3 factors for [ship_class][energy_type].
      Compute: fuel_mass_ton * factor1 + fuel_mass_ton * factor2 + fuel_mass_ton * factor3.
      Multiply the total sum by co2_price.

        O_taxes_ship = (fuel_mass_ton * (f1 + f2 + f3)) * co2_price
        """
        taxes_opex = self.get_db_params(self.country_reg, "taxes_opex")
        tax_energy = taxes_opex["tax_energy_c_e"]

        co2_price = tax_energy["co2_price"]

        class_key = self._map_ship_class_to_db_key(self.ship_class)
        energy_key = self.energy_type

        
        if class_key not in tax_energy:
            #wihout taxes
            self.o_taxes = 0.0
            return

        class_table = tax_energy[class_key]

        if energy_key not in class_table:
            self.o_taxes = 0.0
            return

        factors = class_table[energy_key]  # [f1, f2, f3]
        if not isinstance(factors, (list, tuple)) or len(factors) < 3:
            self.o_taxes = 0.0
            return

        f1, f2, f3 = factors[0], factors[1], factors[2]

      


        # Convertir de kg → g
        fuel_mass_ton = self.fuel_mass_kg / 1000

        # Factores
        f1, f2, f3 = factors

        # Cálculo
        summed = fuel_mass_ton * f1 + fuel_mass_ton * f2 + fuel_mass_ton * f3
        self.o_taxes = summed * co2_price


    # ==================== O_PORTS SHIP ====================

    def compute_o_ports_ship(self):
        """
        - Take the ship size and type (ship_class) → this gives the database key inside 'ports'.
        - For each factor in the vector:
          port_parameters[i] * port_discounts[i]
          and then sum all those products.
        - Multiply the final sum by GT.
        - This gives O_ports_ship.

            O_ports_ship = (Σ_i port_parameters[i] * port_discounts[i]) * GT

        """
        ports_db = self.get_db_params(self.country_oper, "ports")

        class_key = self._map_ship_class_to_db_key(self.ship_class)
        if class_key not in ports_db:
            self.o_ports = 0.0
            return

        port_info = ports_db[class_key]
        params = port_info.get("port_parameters", [])
        discounts = port_info.get("port_discounts", [])

        
        base_factor = 0.0
        for p, d in zip(params, discounts):
            base_factor += p * d

        self.o_ports = base_factor * self.GT

    # ==================== O_INSURANCE SHIP ====================

    def compute_o_insurance_ship(self):
        """
        O_insurance_ship = insurance_rate × (purchase_cost - RV_ship)

        Notes:
        - 'insurance_per_type' is used in the France database.
        - In other countries (e.g., Germany), insurance may come from 'insurance_per_energy'.

        Logic:
        - If 'insurance_per_type' exists and ship_class is found there → use that rate.
        - Else, if 'insurance_per_

        """

        insurance_db = self.get_db_params(self.country_reg, "insurance")

        class_key = self._map_ship_class_to_db_key(self.ship_class)
        energy_key = self.energy_type

        insurance_rate = 0.0

        per_type = insurance_db.get("insurance_per_type")
        if isinstance(per_type, dict) and class_key in per_type:
            insurance_rate = per_type[class_key]
        else:
            per_energy = insurance_db.get("insurance_per_energy", {})
            insurance_rate = per_energy.get(energy_key, 0.0)

        RV_ship = 0.0  #lucho
        self.o_insurance = insurance_rate * (self.purchase_cost - RV_ship)

    # ==================== O_CREW SHIP ====================

    def compute_o_crew_ship(self):
        """
O_crew_ship = Σ (base_wage_per_seafarer × rank_coefficient × team_size)

Explanation:

- The database provides:
        crew.wage_of_crew_rank.wage_per_seafarer - the base yearly wage for one crew member.
        crew.wage_by_rank[ship_class][rank] - a coefficient that adjusts the wage depending on rank.

        - For each crew member in crew_list:
        rank_coefficient = wage_by_rank[ship_class][rank]
        team_size = number of people with that rank
        contribution = base_wage_per_seafarer × rank_coefficient × team_size

        - Sum all contributions for every rank.
        - Multiply the final sum by planning_horizon_years (N).

        Final formula:

        O_crew_ship = ( Σ_i [ base_wage × rank_coef_i × team_size_i ]_]()_

        """

        crew_db = self.get_db_params(self.country_reg, "crew")
        wages = crew_db["wage_of_crew_rank"]
        seafarer_wage = wages.get("seafarer", 0.0)

        if self.crew_monthly_total and self.crew_monthly_total > 0:
            annual_cost = self.crew_monthly_total * 12.0
        else:
            total_crew = 0
            for member in self.crew_list:
                total_crew += member.get("team_size", 0)
            # seafarer_wage annual
            annual_cost = seafarer_wage * total_crew

        self.o_crew = annual_cost * self.planning_horizon_years

    # ==================== O_MAINTENANCE SHIP ====================

    def compute_o_maintenance_ship(self):
        """
        O_maintenance_ship = (O_taxes + O_ports + O_insurance + O_crew + O_energy) × maintenance_rate

            Explanation:

            - Maintenance is no longer a simple constant value.
            - The database provides: maintenance[ship_class] → a maintenance rate specific to the vessel type.
                Example keys: ro_pax_small, ro_pax_medium, fishing_large, ctv_small, etc.

            - Steps:
                1. Retrieve maintenance_rate = maintenance[ship_class].
                2. Compute the sum of all previous OPEX components:
                    base_sum = O_taxes + O_ports + O_insurance + O_crew + O_energy
                3. Multiply that total by the maintenance rate.

            Final formula:

            O_maintenance_ship = base_sum × maintenance_rate
        """
        maintenance_db = self.get_db_params(self.country_oper, "maintenance")

        class_key = self._map_ship_class_to_db_key(self.ship_class)
        maintenance_rate = maintenance_db.get(class_key, 0.0)

        base_sum = (
            self.o_taxes
            + self.o_ports
            + self.o_insurance
            + self.o_crew
            + self.o_energy
        )

        self.o_maintenance = base_sum * maintenance_rate

    # ==================== O_ENERGY SHIP ====================

    def compute_o_energy_ship(self):
        """
        O_energy_ship = annual_energy_consumption_kWh × energy_price

        Explanation:

        - Energy cost is computed directly from the annual energy consumption provided
        by the digital twin (annual_energy_consumption_kWh).

        - The database contains:
            energy.energy_price_c_e[energy_type]
        which gives the price of the selected fuel or energy source.

        - Steps:
            1. Retrieve energy_price = energy_price_c_e[energy_type].
            2. Multiply:
                O_energy_ship = annual_energy_consumption_kWh × energy_price

        This produces the annual operational energy cost for the vessel.
        """

        energy_db = self.get_db_params(self.country_oper, "energy")
        prices = energy_db["energy_price_c_e"]
        energy_price = prices.get(self.energy_type, 0.0)

        self.o_energy = self.annual_energy_consumption_kWh * energy_price


    ######################### MAIN COMPUTE ###########################################

    def compute(self):
        """
        Main compute method for ships:
          OPEX_ship = O_taxes + O_ports + O_insurance + O_crew + O_maintenance + O_energy
        """
        
        p = self.opex_ship

        # calculate by module (IMPORTANTE: mantenimiento va después de los demás)
        self.compute_o_taxes_ship()
        self.compute_o_ports_ship()
        self.compute_o_insurance_ship()
        self.compute_o_crew_ship()
        self.compute_o_energy_ship()
        self.compute_o_maintenance_ship()

        # Total OPEX
        self.o_opex_total = (
            self.o_taxes
            + self.o_ports
            + self.o_insurance
            + self.o_crew
            + self.o_maintenance
            + self.o_energy
        )

        # Populate port outputs
        p.country_reg = self.country_reg
        p.country_oper = self.country_oper
        p.ship_class = self.ship_class
        p.length = self.length
        p.energy_type = self.energy_type
        p.purchase_cost = self.purchase_cost
        p.safety_class = self.safety_class
        p.annual_distance = self.annual_distance
        p.GT = self.GT

        p.n_trips_per_year = self.n_trips_per_year
        p.days_per_trip = self.days_per_trip

        p.planning_horizon_years = self.planning_horizon_years
        p.maintenance_cost_annual = self.maintenance_cost_annual
        p.crew_monthly_total = self.crew_monthly_total

        p.I_energy = self.I_energy
        p.EF_CO2 = self.EF_CO2
        p.NOxSOx_rate = self.NOxSOx_rate
        p.annual_energy_consumption_kWh = self.annual_energy_consumption_kWh
        p.fuel_mass_kg = self.fuel_mass_kg

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
            "GT": self.GT,
            "n_trips_per_year": self.n_trips_per_year,
            "days_per_trip": self.days_per_trip,
            "planning_horizon_years": self.planning_horizon_years,
            "maintenance_cost_annual": self.maintenance_cost_annual,
            "crew_monthly_total": self.crew_monthly_total,
            "crew_list": self.crew_list,
            "I_energy": self.I_energy,
            "EF_CO2": self.EF_CO2,
            "NOxSOx_rate": self.NOxSOx_rate,
            "annual_energy_consumption_kWh": self.annual_energy_consumption_kWh,
            "fuel_mass_kg": self.fuel_mass_kg,
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


# ============================= SCENARIOS INPUTS =====================

def run_ship_scenario(
    scenario_name: str,
    inputs_path: str = "inputs_ship.json",
    db_path: str = "db_ships.json",
):
    print("\n" + "#" * 80)
    print(f"### RUNNING SHIP SCENARIO: {scenario_name} ###")
    print("#" * 80)

    
    inputs_full_path = os.path.join(BASE_DIR, inputs_path)
    db_full_path = os.path.join(BASE_DIR, db_path)

    # Load scenarios
    with open(inputs_full_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    scenarios = all_data.get("scenarios", [])

    # name by scenario
    scenario = None
    for sc in scenarios:
        if sc.get("name") == scenario_name:
            scenario = sc
            break

    if scenario is None:
        raise ValueError(f"Scenario '{scenario_name}' not found in {inputs_full_path}")

    # Cosapp system
    sys_ship = ShipOPEXCalculator("ship_opex_case", db_path=db_full_path)

    
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

    # Execute
    driver = sys_ship.add_driver(RunOnce("run"))
    sys_ship.run_drivers()

    # Print results
    print("\n--- SHIP OPEX RESULTS ---")
    print(f"O_taxes:       {sys_ship.o_taxes:.2f} €")
    print(f"O_ports:       {sys_ship.o_ports:.2f} €")
    print(f"O_insurance:   {sys_ship.o_insurance:.2f} €")
    print(f"O_crew:        {sys_ship.o_crew:.2f} €")
    print(f"O_maintenance: {sys_ship.o_maintenance:.2f} €")
    print(f"O_energy:      {sys_ship.o_energy:.2f} €")
    print(f"OPEX_total:    {sys_ship.o_opex_total:.2f} €")

    # Save scenarios in json
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

   # Choose any scenario defined in inputs_ship.json

    run_ship_scenario("scenario1_ro_pax_large_diesel_france")
    # run_ship_scenario("scenario2_ro_pax_medium_diesel_spain")
    # run_ship_scenario("scenario3_ro_pax_small_BET_germany")
    # run_ship_scenario("scenario4_fishing_small_diesel_italy")

    print("\n\n========================================")
