"""
Unified CosApp OPEX Calculator for SHIPS and TRUCKS.

You choose:
    asset_type = "ship"  -> uses ShipOPEXCalculator + db_ships.json + inputs_ship.json
    asset_type = "truck" -> uses TruckOPEXCalculator + db_trucks.json + inputs_trucks.json

The internal equations, nomenclature and structure of each calculator
are preserved. Only orchestration / scenario loading is unified.
"""

import json
import sys
import os

from cosapp.base import System
from cosapp.ports import Port
from cosapp.drivers import RunOnce

# -----------------------------------------------------------------------------
# Console encoding fix (Windows)
# -----------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# SHIP PART  (your code, reorganized but with same logic)
# =============================================================================

SHIP_CLASS_TO_DB_KEY = {
    "large": "ro_pax_large",
    "big": "ro_pax_large",
    "cargo_large": "ro_pax_large",
}


class ShipOPEXPort(Port):
    """Port for OPEX calculation inputs and outputs for ships."""

    def setup(self):
        # -------------------- USER INPUTS (ORANGE) --------------------
        self.add_variable("country_reg", dtype=str, desc="Country of registration")
        self.add_variable("country_oper", dtype=str, desc="Country of operation")

        self.add_variable(
            "ship_class",
            dtype=str,
            desc=(
                "Ship class key used in DB "
                "(ro_pax_small, fishing_large, ctv_medium, ro_pax, small, medium, large, ctv...)"
            ),
        )
        self.add_variable("length", dtype=float, desc="Ship length in meters")
        self.add_variable("energy_type", dtype=str, desc="Type of energy (DIESEL, BET, FCET...)")
        self.add_variable("purchase_cost", dtype=float, desc="Purchase cost in EUR")
        self.add_variable("safety_class", dtype=str, desc="Safety class")
        self.add_variable(
            "annual_distance", dtype=float, desc="Annual distance travelled (km or nm)"
        )

        # Gross tonnage (nuevo input)
        self.add_variable("GT", dtype=float, desc="Gross tonnage (GT) of the ship")

        # Ports / trips
        self.add_variable("n_trips_per_year", dtype=float, desc="Number of trips per year")
        self.add_variable("days_per_trip", dtype=float, desc="Number of days per trip")

        # Crew
        self.add_variable("planning_horizon_years", dtype=float, desc="Number of years N")
        self.add_variable(
            "maintenance_cost_annual",
            dtype=float,
            desc="Annual maintenance cost in EUR (legacy)",
        )
        self.add_variable(
            "crew_monthly_total",
            dtype=float,
            desc="Total monthly crew cost (EUR). If 0, use seafarer * crew size.",
        )

        # -------------------- DIGITAL TWIN / USER ENV (ORANGE) --------------------
        self.add_variable("I_energy", dtype=float, desc="Energy consumption per km (MWh/km or ton/km)")
        self.add_variable(
            "EF_CO2",
            dtype=float,
            desc="CO2 emission factor per unit of energy (kg CO2 / kWh or per ton)",
        )
        self.add_variable(
            "NOxSOx_rate",
            dtype=float,
            desc="NOx/SOx emission per km (kg/km)",
        )
        self.add_variable(
            "annual_energy_consumption_kWh",
            dtype=float,
            desc="Annual energy consumption retrieved from digital twin (kWh)",
        )

        # fuel mass: inward in kg, converted to ton in formulas
        self.add_variable(
            "fuel_mass_kg",
            dtype=float,
            desc="Fuel mass used in a period (kg), provided by digital twin",
        )

        # -------------------- OUTPUTS (GREEN) --------------------
        self.add_variable("o_taxes", dtype=float, desc="Total annual taxes for ship in EUR")
        self.add_variable("o_ports", dtype=float, desc="Total annual ports costs in EUR")
        self.add_variable("o_insurance", dtype=float, desc="Total annual insurance in EUR")
        self.add_variable("o_crew", dtype=float, desc="Total crew cost in EUR")
        self.add_variable("o_maintenance", dtype=float, desc="Annual maintenance in EUR")
        self.add_variable("o_energy", dtype=float, desc="Annual energy cost in EUR")
        self.add_variable("o_opex_total", dtype=float, desc="Total OPEX for ship in EUR")


class ShipOPEXCalculator(System):
    """CosApp System for ship OPEX."""

    def setup(self, db_path: str = "db_ships.json"):
        # -------------------- DATA BASE SHIPS (YELLOW) --------------------
        db_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "database", "db_ships.json"))

        with open(db_full_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        object.__setattr__(
            self,
            "_countries_data",
            {c["country"]: c for c in db_data["countries"]},
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

        # GT
        self.add_inward("GT", 0.0, dtype=float)

        self.add_inward("n_trips_per_year", 10.0, dtype=float)
        self.add_inward("days_per_trip", 5.0, dtype=float)

        self.add_inward("planning_horizon_years", 1.0, dtype=float)
        self.add_inward("maintenance_cost_annual", 100_000.0, dtype=float)
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
            desc="Annual energy consumption from digital twin simulation",
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

        # Support both "taxes_opex" and "taxes"
        if category in ("taxes_opex", "taxes"):
            if "taxes_opex" in country_db:
                return country_db["taxes_opex"]
            if "taxes" in country_db:
                return country_db["taxes"]
            raise ValueError(f"No 'taxes_opex' or 'taxes' entry for country '{country}'")

        if category in country_db:
            return country_db[category]

        raise ValueError(f"Category '{category}' not found for country '{country}'")

    def _map_ship_class_to_db_key(self, ship_class: str) -> str:
        
        return SHIP_CLASS_TO_DB_KEY.get(ship_class, ship_class)

    # ==================== O_TAXES SHIP ====================

    def compute_o_taxes_ship(self):
        """
        O_taxes_ship = (fuel_mass_ton * (f1 + f2 + f3)) * co2_price

        fuel_mass_ton = fuel_mass_kg / 1000
        """
        taxes_opex = self.get_db_params(self.country_reg, "taxes_opex")
        tax_energy = taxes_opex["tax_energy_c_e"]

        co2_price = tax_energy["co2_price"]

        class_key = self._map_ship_class_to_db_key(self.ship_class)
        energy_key = self.energy_type

        if class_key not in tax_energy:
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

        # Convert kg → ton
        fuel_mass_ton = self.fuel_mass_kg / 1000.0

        f1, f2, f3 = factors
        summed = fuel_mass_ton * f1 + fuel_mass_ton * f2 + fuel_mass_ton * f3
        self.o_taxes = summed * co2_price

    # ==================== O_PORTS SHIP ====================

    def compute_o_ports_ship(self):
        """
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

        Logic:
        - If insurance_per_type and ship_class exists → use it.
        - Else if insurance_per_energy and energy_type exists → use it.
        - Else 0.
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

        RV_ship = 0.0  # (placeholder for future RV integration)
        self.o_insurance = insurance_rate * (self.purchase_cost - RV_ship)

    # ==================== O_CREW SHIP ====================

    def compute_o_crew_ship(self):
        """
        O_crew_ship = annual_cost × planning_horizon_years

        annual_cost:
          - if crew_monthly_total > 0 → crew_monthly_total * 12
          - else: seafarer_wage * total_crew
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
            annual_cost = seafarer_wage * total_crew

        self.o_crew = annual_cost * self.planning_horizon_years

    # ==================== O_MAINTENANCE SHIP ====================

    def compute_o_maintenance_ship(self):
        """
        O_maintenance_ship = (O_taxes + O_ports + O_insurance + O_crew + O_energy) × maintenance_rate
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
        O_energy_ship = annual_energy_consumption_kWh (digital twin) × energy_price
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

        self.compute_o_taxes_ship()
        self.compute_o_ports_ship()
        self.compute_o_insurance_ship()
        self.compute_o_crew_ship()
        self.compute_o_energy_ship()
        self.compute_o_maintenance_ship()

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
        """Save results from ships."""
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


def run_ship_scenario(
    scenario_name: str,
    inputs_path: str = "inputs\inputs_opex.json",
    db_path: str = "database\db_ships.json",
):
    """Load a ship scenario from JSON and run ShipOPEXCalculator."""
    print("\n" + "#" * 80)
    print(f"### RUNNING SHIP SCENARIO: {scenario_name} ###")
    print("#" * 80)

    inputs_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "inputs", "inputs_opex.json"))

#                                                             

    db_full_path = db_path  # joined in ShipOPEXCalculator.setup

    with open(inputs_full_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    scenarios = all_data.get("scenarios", [])
    scenario = None
    for sc in scenarios:
        if sc.get("name") == scenario_name:
            scenario = sc
            break

    if scenario is None:
        raise ValueError(f"Scenario '{scenario_name}' not found in {inputs_full_path}")

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

    driver = sys_ship.add_driver(RunOnce("run"))
    sys_ship.run_drivers()

    print("\n--- SHIP OPEX RESULTS ---")
    print(f"O_taxes:       {sys_ship.o_taxes:.2f} €")
    print(f"O_ports:       {sys_ship.o_ports:.2f} €")
    print(f"O_insurance:   {sys_ship.o_insurance:.2f} €")
    print(f"O_crew:        {sys_ship.o_crew:.2f} €")
    print(f"O_maintenance: {sys_ship.o_maintenance:.2f} €")
    print(f"O_energy:      {sys_ship.o_energy:.2f} €")
    print(f"OPEX_total:    {sys_ship.o_opex_total:.2f} €")

    safe_name = scenario_name.replace(" ", "_")
    out_json = os.path.join(BASE_DIR, f"resultado_opex_ship_{safe_name}.json")
    sys_ship.save_results_to_json(out_json)
    print(f"Resultados guardados en: {out_json}")

    return sys_ship


# =============================================================================
# TRUCK PART  
# =============================================================================


class OPEXPort(Port):
    """Port for OPEX calculation inputs and outputs (trucks)."""

    def setup(self):
        # User Inputs (Orange arrows in diagrams)
        self.add_variable("purchase_cost", dtype=float, desc="Purchase cost in EUR")
        self.add_variable("type_energy", dtype=str, desc="Type of energy")
        self.add_variable("size_vehicle", dtype=str, desc="Vehicle class (N1, N2, N3)")
        self.add_variable("registration_country", dtype=str, desc="Registration country")
        self.add_variable("annual_distance_travel", dtype=float, desc="Annual distance in km")
        self.add_variable("departure_city", dtype=str, desc="Departure city")
        self.add_variable("arrival_city", dtype=str, desc="Arrival city")
        self.add_variable("RV", dtype=float, desc="Residual Value in EUR")
        self.add_variable("N_years", dtype=float, desc="Number of years")
        self.add_variable("team_count", dtype=int, desc="Number of drivers (always 1 for trucks)")
        self.add_variable("maintenance_cost", dtype=float, desc="Annual maintenance cost in EUR")

        # Digital Twin Simulation Outputs (Orange)
        self.add_variable(
            "consumption_energy",
            dtype=float,
            desc="Energy consumption (kWh or liters)",
        )
        self.add_variable("fuel_multiplier", dtype=float, desc="Fuel multiplier from DTS")
        self.add_variable("EF_CO2_diesel", dtype=float, desc="CO2 emission factor kg/km")

        # Outputs (Green)
        self.add_variable("o_taxes", dtype=float, desc="Total annual taxes in EUR")
        self.add_variable("o_tolls", dtype=float, desc="Total tolls cost in EUR")
        self.add_variable("o_insurance", dtype=float, desc="Total insurance cost in EUR")
        self.add_variable("o_crew", dtype=float, desc="Total crew cost in EUR")
        self.add_variable("o_energy", dtype=float, desc="Total energy cost in EUR")
        self.add_variable("o_opex_total", dtype=float, desc="Total OPEX in EUR")


class TruckOPEXCalculator(System):
    """
    CosApp System for calculating truck OPEX costs.
    
    """

    def setup(self, db_path: str = "database\db_trucks.json"):
        # Load database
        db_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "database", "db_trucks.json"))

        with open(db_full_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        object.__setattr__(
            self,
            "_countries_data",
            {c["country"]: c["data_country"] for c in db_data["countries"]},
        )

        # Add port
        self.add_inward("opex", OPEXPort, desc="OPEX calculation port")

        # USER INPUTS (Orange arrows)
        self.add_inward("purchase_cost", 150000.0, desc="Purchase cost in EUR")
        self.add_inward("type_energy", "diesel", dtype=str, desc="Type of energy")
        self.add_inward("size_vehicle", "N3", dtype=str, desc="Vehicle class")
        self.add_inward("registration_country", "France", dtype=str, desc="Registration country")
        self.add_inward("annual_distance_travel", 80000.0, desc="Annual distance in km")
        self.add_inward("departure_city", "Paris", dtype=str, desc="Departure city")
        self.add_inward("arrival_city", "Lyon", dtype=str, desc="Arrival city")
        self.add_inward("RV", 50000.0, desc="Residual Value in EUR")
        self.add_inward("N_years", 1.0, desc="Number of years")
        self.add_inward("team_count", 1, desc="Number of drivers")
        self.add_inward("maintenance_cost", 5000.0, desc="Annual maintenance in EUR")

        # DIGITAL TWIN SIMULATION OUTPUTS (Orange)
        self.add_inward("consumption_energy", 28000.0, desc="Energy consumption kWh or liters")
        self.add_inward("fuel_multiplier", 1.0, desc="Fuel multiplier from DTS")
        self.add_inward("EF_CO2_diesel", 0.85, desc="CO2 emission factor kg/km")

        # OUTPUTS (Green)
        self.add_outward("o_taxes", 0.0, desc="Total annual taxes in EUR")
        self.add_outward("o_tolls", 0.0, desc="Total tolls cost in EUR")
        self.add_outward("o_insurance", 0.0, desc="Total insurance cost in EUR")
        self.add_outward("o_crew", 0.0, desc="Total crew cost in EUR")
        self.add_outward("o_energy", 0.0, desc="Total energy cost in EUR")
        self.add_outward("o_opex_total", 0.0, desc="Total OPEX in EUR")

    # ==================== DATABASE ACCESS METHODS ====================

    def get_db_params(self, country: str, category: str):
        """Get database parameters for a specific category."""
        if country not in self._countries_data:
            raise ValueError(f"Country '{country}' not found in database")
        return self._countries_data[country][category]

    # ==================== O_TAXES CALCULATION ====================

    def compute_o_taxes(self):
        """
        O_taxes = consumption_energy × price_energy_km × tax_energy × fuel_multiplier ×
                  EF_CO2 × tax_CO2 × regional_coefficient + tax_reg + tax_annual + B_env
        """
        taxes_db = self.get_db_params(self.registration_country, "taxes")

        price_energy_km = taxes_db["price_energy_km"]
        tax_energy = taxes_db["tax_energy_c_e"].get(self.type_energy, 1.0)
        tax_reg = taxes_db["tax_reg_c_k_L"].get(self.size_vehicle, 0.0)
        tax_annual = taxes_db["tax_annual_c_k_L"].get(self.size_vehicle, 0.0)
        regional_coefficient = taxes_db["regional_coefficient"]
        tax_CO2 = taxes_db["tax_CO2_c_e"]
        B_env = taxes_db["B_env_c_k_e"].get(self.type_energy, 0.0)

        variable_taxes = (
            self.consumption_energy
            * price_energy_km
            * tax_energy
            * self.fuel_multiplier
            * self.EF_CO2_diesel
            * tax_CO2
            * regional_coefficient
        )
        fixed_taxes = tax_reg + tax_annual + B_env

        self.o_taxes = variable_taxes + fixed_taxes

    # ==================== O_TOLLS CALCULATION ====================

    def compute_o_tolls(self):
        """
        O_tolls = price_per_km × annual_distance_travel
        """
        tolls_db = self.get_db_params(self.registration_country, "tolls")

        if self.size_vehicle not in tolls_db["price_per_km"]:
            raise ValueError(
                f"Vehicle class '{self.size_vehicle}' not found in tolls database"
            )

        if self.type_energy not in tolls_db["price_per_km"][self.size_vehicle]:
            raise ValueError(
                f"Energy type '{self.type_energy}' not found for vehicle class"
            )

        price_per_km = tolls_db["price_per_km"][self.size_vehicle][self.type_energy]

        self.o_tolls = price_per_km * self.annual_distance_travel

    # ==================== O_INSURANCE CALCULATION ====================

    def compute_o_insurance(self):
        """
        O_insurance = insurance_rate × (purchase_cost - RV)
        """
        insurance_db = self.get_db_params(self.registration_country, "insurance")

        if self.type_energy not in insurance_db["insurance_rate_c_L_e_safety"]:
            raise ValueError(
                f"Energy type '{self.type_energy}' not found in insurance database"
            )

        insurance_rate = insurance_db["insurance_rate_c_L_e_safety"][self.type_energy]

        self.o_insurance = insurance_rate * (self.purchase_cost - self.RV)

    # ==================== O_CREW CALCULATION ====================

    def compute_o_crew(self):
        """
        O_crew = wage_of_driver × N_years × team_count
        """
        crew_db = self.get_db_params(self.registration_country, "crew")
        wage_of_driver = crew_db["wage_of_crew_rank"]["driver"]

        self.o_crew = wage_of_driver * self.N_years * self.team_count

    # ==================== O_ENERGY CALCULATION ====================

    def compute_o_energy(self):
        """
        O_energy = consumption_energy × energy_price
        """
        energy_db = self.get_db_params(self.registration_country, "energy")

        if self.type_energy not in energy_db["energy_price_c_e"]:
            raise ValueError(
                f"Energy type '{self.type_energy}' not found in energy database"
            )

        energy_price = energy_db["energy_price_c_e"][self.type_energy]

        self.o_energy = self.consumption_energy * energy_price

    # ==================== MAIN COMPUTE ====================

    def compute(self):
        """
        Total OPEX = O_taxes + O_tolls + O_insurance + O_crew + O_energy + maintenance_cost
        """
        self.compute_o_taxes()
        self.compute_o_tolls()
        self.compute_o_insurance()
        self.compute_o_crew()
        self.compute_o_energy()

        self.o_opex_total = (
            self.o_taxes
            + self.o_tolls
            + self.o_insurance
            + self.o_crew
            + self.o_energy
            + self.maintenance_cost
        )

    # ---------------- SMALL HELPERS (printing/saving) ----------------

    def print_results(self):
        """Print calculation results in a formatted way."""
        print("\n" + "=" * 80)
        print("TRUCK OPEX CALCULATION RESULTS")
        print("=" * 80)
        print(f"Country: {self.registration_country}")
        print(f"Vehicle Class: {self.size_vehicle}")
        print(f"Energy Type: {self.type_energy}")
        print(f"Annual Distance: {self.annual_distance_travel:.2f} km")
        print(f"Purchase Cost: {self.purchase_cost:.2f} EUR")
        print(f"Residual Value: {self.RV:.2f} EUR")
        print(f"Number of Years: {self.N_years:.1f}")
        print("-" * 80)

        print("\n--- O_TAXES (Annual Operating Taxes) ---")
        print(f"→ TOTAL O_TAXES: {self.o_taxes:.2f} EUR/year")

        print("\n--- O_TOLLS (Road Tolls) ---")
        print(f"→ TOTAL O_TOLLS: {self.o_tolls:.2f} EUR")

        print("\n--- O_INSURANCE ---")
        print(f"→ TOTAL O_INSURANCE: {self.o_insurance:.2f} EUR/year")

        print("\n--- O_CREW (Driver Wages) ---")
        print(f"→ TOTAL O_CREW: {self.o_crew:.2f} EUR")

        print("\n--- O_ENERGY (Fuel/Electricity Costs) ---")
        print(f"→ TOTAL O_ENERGY: {self.o_energy:.2f} EUR")

        print("\n--- O_MAINTENANCE ---")
        print(f"Annual Maintenance: {self.maintenance_cost:.2f} EUR/year")

        print("\n" + "=" * 80)
        print(f"TOTAL OPEX: {self.o_opex_total:.2f} EUR")
        print("=" * 80 + "\n")


def run_truck_scenario(
    scenario_name: str,
    inputs_path: str = "inputs\inputs_opex.json",
    db_path: str = "database\db_trucks.json",
):
    
    print("\n" + "#" * 80)
    print(f"### RUNNING TRUCK SCENARIO: {scenario_name} ###")
    print("#" * 80)

    inputs_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "inputs", "inputs_opex.json"))


    db_full_path = db_path  

    with open(inputs_full_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    scenarios = all_data.get("scenarios", [])
    scenario = None
    for sc in scenarios:
        if sc.get("name") == scenario_name:
            scenario = sc
            break

    if scenario is None:
        raise ValueError(f"Scenario '{scenario_name}' not found in {inputs_full_path}")

    sys_truck = TruckOPEXCalculator("truck_opex_case", db_path=db_full_path)

    for key, value in scenario.items():
        if key in ("name", "description"):
            continue
        if not hasattr(sys_truck, key):
            continue

        current = getattr(sys_truck, key)
        try:
            if isinstance(current, (float, int)) and isinstance(value, (int, float)):
                value = type(current)(value)
            elif isinstance(current, str):
                value = str(value)
        except Exception:
            pass

        setattr(sys_truck, key, value)

    driver = sys_truck.add_driver(RunOnce("run"))
    sys_truck.run_drivers()

    sys_truck.print_results()

    # save compact JSON of main outputs
    out_json = os.path.join(
        BASE_DIR,
        f"resultado_opex_truck_{scenario_name.replace(' ', '_')}.json",
    )
    data_out = {
        "purchase_cost": sys_truck.purchase_cost,
        "type_energy": sys_truck.type_energy,
        "size_vehicle": sys_truck.size_vehicle,
        "registration_country": sys_truck.registration_country,
        "annual_distance_travel": sys_truck.annual_distance_travel,
        "RV": sys_truck.RV,
        "N_years": sys_truck.N_years,
        "maintenance_cost": sys_truck.maintenance_cost,
        "consumption_energy": sys_truck.consumption_energy,
        "fuel_multiplier": sys_truck.fuel_multiplier,
        "EF_CO2_diesel": sys_truck.EF_CO2_diesel,
        "o_taxes": sys_truck.o_taxes,
        "o_tolls": sys_truck.o_tolls,
        "o_insurance": sys_truck.o_insurance,
        "o_crew": sys_truck.o_crew,
        "o_energy": sys_truck.o_energy,
        "o_opex_total": sys_truck.o_opex_total,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data_out, f, indent=4, ensure_ascii=False)

    print(f"Truck OPEX results saved to: {out_json}")

    return sys_truck


######################### OPEX CALCULATOR SELECTOR #########################

def run_opex_scenario(
    scenario_name: str,
    inputs_path: str = "inputs_opex.json",
):
    """
    Dispatcher: read scenario and run either ShipOPEXCalculator or TruckOPEXCalculator
      - if 'ship_class' -> ShipOPEXCalculator
      - if 'size_vehicle' -> TruckOPEXCalculator
    """
    inputs_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "inputs", "inputs_opex.json"))

#                                                             



    with open(inputs_full_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    scenarios = all_data.get("scenarios", [])
    scenario = None
    for sc in scenarios:
        if sc.get("name") == scenario_name:
            scenario = sc
            break

    if scenario is None:
        raise ValueError(f"Scenario '{scenario_name}' not found in {inputs_full_path}")

    
    if "ship_class" in scenario:
        
        return run_ship_scenario(scenario_name, inputs_path=inputs_path)
    elif "size_vehicle" in scenario:
        
        return run_truck_scenario(scenario_name, inputs_path=inputs_path)
    else:
        raise ValueError(
            f"Scenario '{scenario_name}' does not look like ship or truck "
            f"(no 'ship_class' or 'size_vehicle' keys)."
        )



# =============================================================================
# MAIN SELECTOR: one place to choose SHIP or TRUCK
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Unified CosApp OPEX Calculator - SHIPS & TRUCKS (inputs_opex.json)")
    print("=" * 80)


    # Chose scenario to run from inputs_opex.json:
    #  - scenario1_ro_pax_large_diesel_france
    #  - scenario2_ro_pax_medium_diesel_spain
    #  - scenario3_ro_pax_small_BET_germany
    #  - scenario4_fishing_small_diesel_italy
    #  - scenario1_truck_diesel_france
    #  - scenario2_truck_electric_germany
    #  - scenario3_truck_h2_spain
    #  - scenario4_truck_hybrid_italy

    scenario_name = "scenario1_ro_pax_large_diesel_france"
    #scenario_name = "scenario1_truck_diesel_france"
    run_opex_scenario(scenario_name)

    
