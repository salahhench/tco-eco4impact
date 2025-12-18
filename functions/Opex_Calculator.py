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

from models.vehicle_port import VehiclePropertiesPort
from models.country_port import CountryPropertiesPort

# -----------------------------------------------------------------------------
# Console encoding fix (Windows)
# -----------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# SHIP PART  (Logic preserved)
# =============================================================================

SHIP_CLASS_TO_DB_KEY = {
    "large": "ro_pax_large",
    "big": "ro_pax_large",
    "cargo_large": "ro_pax_large",
}

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

        # -------------------- PORTS --------------------
        self.add_input(VehiclePropertiesPort, 'in_vehicle_properties')
        self.add_input(CountryPropertiesPort, 'in_country_properties')


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
        vp = self.in_vehicle_properties
        taxes_opex = self.get_db_params(vp.registration_country, "taxes_opex")
        tax_energy = taxes_opex["tax_energy_c_e"]
        co2_price = tax_energy["co2_price"]

        class_key = self._map_ship_class_to_db_key(vp.ship_class)
        energy_key = vp.type_energy

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
        fuel_mass_ton = vp.fuel_mass_kg / 1000.0

        f1, f2, f3 = factors
        summed = fuel_mass_ton * f1 + fuel_mass_ton * f2 + fuel_mass_ton * f3
        self.o_taxes = summed * co2_price

    # ==================== O_PORTS SHIP ====================

    def compute_o_ports_ship(self):
        vp = self.in_vehicle_properties
        ports_db = self.get_db_params(vp.country_oper, "ports")

        class_key = self._map_ship_class_to_db_key(vp.ship_class)
        if class_key not in ports_db:
            self.o_ports = 0.0
            return

        port_info = ports_db[class_key]
        params = port_info.get("port_parameters", [])
        discounts = port_info.get("port_discounts", [])

        base_factor = 0.0
        for p, d in zip(params, discounts):
            base_factor += p * d

        self.o_ports = base_factor * vp.GT

    # ==================== O_INSURANCE SHIP ====================

    def compute_o_insurance_ship(self):
        vp = self.in_vehicle_properties
        insurance_db = self.get_db_params(vp.registration_country, "insurance")

        class_key = self._map_ship_class_to_db_key(vp.ship_class)
        energy_key = vp.type_energy

        insurance_rate = 0.0

        per_type = insurance_db.get("insurance_per_type")
        if isinstance(per_type, dict) and class_key in per_type:
            insurance_rate = per_type[class_key]
        else:
            per_energy = insurance_db.get("insurance_per_energy", {})
            insurance_rate = per_energy.get(energy_key, 0.0)

        RV_ship = 0.0 
        self.o_insurance = insurance_rate * (vp.purchase_cost - RV_ship)

    # ==================== O_CREW SHIP ====================

    def compute_o_crew_ship(self):
        vp = self.in_vehicle_properties
        cp = self.in_country_properties
        crew_db = self.get_db_params(vp.registration_country, "crew")
        wages = crew_db["wage_of_crew_rank"]
        seafarer_wage = wages.get("seafarer", 0.0)

        if cp.crew_monthly_total and cp.crew_monthly_total > 0:
            annual_cost = cp.crew_monthly_total * 12.0
        else:
            total_crew = 0
            for member in vp.crew_list:
                total_crew += member.get("team_size", 0)
            annual_cost = seafarer_wage * total_crew

        self.o_crew = annual_cost

    # ==================== O_MAINTENANCE SHIP ====================

    def compute_o_maintenance_ship(self):
        vp = self.in_vehicle_properties
        maintenance_db = self.get_db_params(vp.country_oper, "maintenance")

        class_key = self._map_ship_class_to_db_key(vp.ship_class)
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
        vp = self.in_vehicle_properties
        energy_db = self.get_db_params(vp.country_oper, "energy")
        prices = energy_db["energy_price_c_e"]
        energy_price = prices.get(vp.type_energy, 0.0)

        self.o_energy = vp.annual_energy_consumption_kWh * energy_price

    # ==================== MAIN COMPUTE SHIP ====================

    def compute(self):
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

    def save_results_to_json(self, filename: str = "resultado_opex_ship.json"):
        vp = self.in_vehicle_properties
        cp = self.in_country_properties
        data_out = {
            "registration_country": vp.registration_country,
            "country_oper": vp.country_oper,
            "ship_class": vp.ship_class,
            "length": vp.length,
            "type_energy": vp.type_energy,
            "purchase_cost": vp.purchase_cost,
            "safety_class": vp.safety_class,
            "annual_distance": vp.annual_distance,
            "GT": vp.GT,
            "n_trips_per_year": vp.n_trips_per_year,
            "days_per_trip": vp.days_per_trip,
            "planning_horizon_years": vp.planning_horizon_years,
            "maintenance_cost_annual": vp.maintenance_cost_annual,
            "crew_monthly_total": cp.crew_monthly_total,
            "crew_list": vp.crew_list,
            "I_energy": vp.I_energy,
            "EF_CO2": vp.EF_CO2,
            "NOxSOx_rate": vp.NOxSOx_rate,
            "annual_energy_consumption_kWh": vp.annual_energy_consumption_kWh,
            "fuel_mass_kg": vp.fuel_mass_kg,
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


# =============================================================================
# TRUCK PART - REVISED & CORRECTED
# =============================================================================

class TruckOPEXCalculator(System):
    """CosApp System for calculating truck OPEX costs."""

    def setup(self, db_path: str = "database\\db_trucks.json"):
        # Load database
        db_full_path = os.path.abspath(os.path.join(BASE_DIR, "..", "database", "db_trucks.json"))

        with open(db_full_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        object.__setattr__(
            self,
            "_countries_data",
            {c["country"]: c for c in db_data["countries"]},
        )

        # Add ports
        self.add_input(VehiclePropertiesPort, 'in_vehicle_properties')
        self.add_input(CountryPropertiesPort, 'in_country_properties')

        # OUTPUTS
        self.add_outward("o_taxes", 0.0, desc="Total annual taxes in EUR")
        self.add_outward("o_tolls", 0.0, desc="Total tolls cost in EUR")
        self.add_outward("o_insurance", 0.0, desc="Total insurance cost in EUR")
        self.add_outward("o_crew", 0.0, desc="Total crew cost in EUR")
        self.add_outward("o_energy", 0.0, desc="Total energy cost in EUR")
        self.add_outward("o_opex_total", 0.0, desc="Total OPEX in EUR")

    # ==================== DATABASE ACCESS METHODS & HELPERS ====================

    def get_country_data(self):
        """Get the full country data."""
        country_name = self.in_vehicle_properties.registration_country
        if country_name not in self._countries_data:
            raise ValueError(f"Country '{country_name}' not found in database")
        return self._countries_data[country_name]

    def normalize_type_energy(self):
        """Normalize energy type to uppercase for database lookup (e.g. 'diesel' -> 'DIESEL')."""
        energy_type = self.in_vehicle_properties.type_energy
        if not energy_type:
            return "DIESEL"
        return energy_type.upper().strip()

    def normalize_vehicle_size(self):
        """Normalize vehicle size to uppercase (e.g. 'n3' -> 'N3')."""
        size_vehicle = self.in_vehicle_properties.size_vehicle
        if not size_vehicle:
            return "N3"
        return size_vehicle.upper().strip()

    # ==================== O_TAXES CALCULATION ====================

    def compute_o_taxes(self):
        """
        O_taxes = variable_taxes + fixed_taxes
        """
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        
        # Normalize keys to match JSON (Case Insensitive Safety)
        energy_key = self.normalize_type_energy()
        vehicle_key = self.normalize_vehicle_size()
        
        # Retrieve Parameters from DB Structure
        # 1. Price energy/km (inside external_factors)
        external_factors = country_data.get("external_factors", {})
        price_energy_km_data = external_factors.get("price_energy_km", {})
        # Default to 'h1' profile
        price_energy_km = price_energy_km_data.get("h1", {}).get(energy_key, 0.0)
        
        # 2. Taxes at root of data_country
        tax_energy = country_data.get("tax_energy_c_e", {}).get(energy_key, 1.0)
        tax_reg = country_data.get("tax_reg_c_k_L", {}).get(vehicle_key, 0.0)
        tax_annual = country_data.get("tax_annual_c_k_L", {}).get(vehicle_key, 0.0)
        regional_coefficient = country_data.get("regional_coefficient", 1.0)
        tax_CO2 = country_data.get("tax_CO2_c_e", 0.0)
        B_env = country_data.get("B_env_c_k_e", {}).get(energy_key, 0.0)

        variable_taxes = (
            vp.consumption_energy
            * price_energy_km
            * tax_energy
            * vp.fuel_multiplier
            * vp.EF_CO2  # Uses the agnostic variable
            * tax_CO2
            * regional_coefficient
        )
        fixed_taxes = tax_reg + tax_annual + B_env

        self.o_taxes = variable_taxes + fixed_taxes

    # ==================== O_TOLLS CALCULATION ====================

    def compute_o_tolls(self):
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        tolls_db = country_data.get("tolls", {})
        
        energy_key = self.normalize_type_energy()
        vehicle_key = self.normalize_vehicle_size()

        if vehicle_key not in tolls_db.get("price_per_km", {}):
            # Fallback or error? defaulting to 0.0 for safety or raising Error
            self.o_tolls = 0.0
            return 

        if energy_key not in tolls_db["price_per_km"][vehicle_key]:
            self.o_tolls = 0.0
            return

        price_per_km = tolls_db["price_per_km"][vehicle_key][energy_key]
        self.o_tolls = price_per_km * vp.annual_distance_travel

    # ==================== O_INSURANCE CALCULATION ====================

    def compute_o_insurance(self):
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        insurance_db = country_data.get("insurance", {})
        energy_key = self.normalize_type_energy()

        rate_table = insurance_db.get("insurance_rate_c_L_e_safety", {})
        if energy_key not in rate_table:
            # Default rate if missing?
            insurance_rate = 0.03 
        else:
            insurance_rate = rate_table[energy_key]

        self.o_insurance = insurance_rate * (vp.purchase_cost - vp.RV)

    # ==================== O_CREW CALCULATION ====================

    def compute_o_crew(self):
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        crew_db = country_data.get("crew", {})
        wage_of_driver = crew_db.get("wage_of_crew_rank", {}).get("driver", 0.0)

        self.o_crew = wage_of_driver  * vp.team_count

    # ==================== O_ENERGY CALCULATION ====================

    def compute_o_energy(self):
        vp = self.in_vehicle_properties
        country_data = self.get_country_data()
        energy_db = country_data.get("energy", {})
        energy_key = self.normalize_type_energy()

        price_table = energy_db.get("energy_price_c_e", {})
        if energy_key not in price_table:
            energy_price = 0.0
        else:
            energy_price = price_table[energy_key]

        self.o_energy = vp.consumption_energy * energy_price

    # ==================== MAIN COMPUTE ====================

    def compute(self):
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
            + self.in_vehicle_properties.maintenance_cost_annual
        )

    def print_results(self):
        vp = self.in_vehicle_properties
        print("\n" + "=" * 80)
        print("TRUCK OPEX CALCULATION RESULTS")
        print("=" * 80)
        print(f"Country: {vp.registration_country}")
        print(f"Vehicle Class: {vp.size_vehicle}")
        print(f"Energy Type: {vp.type_energy}")
        print(f"Annual Distance: {vp.annual_distance_travel:.2f} km")
        print(f"Purchase Cost: {vp.purchase_cost:.2f} EUR")
        print("-" * 80)
        print(f"→ TOTAL O_TAXES: {self.o_taxes:.2f} EUR")
        print(f"→ TOTAL O_TOLLS: {self.o_tolls:.2f} EUR")
        print(f"→ TOTAL O_INSURANCE: {self.o_insurance:.2f} EUR")
        print(f"→ TOTAL O_CREW: {self.o_crew:.2f} EUR")
        print(f"→ TOTAL O_ENERGY: {self.o_energy:.2f} EUR")
        print(f"→ Annual Maintenance: {vp.maintenance_cost_annual:.2f} EUR")
        print("\n" + "=" * 80)
        print(f"TOTAL OPEX: {self.o_opex_total:.2f} EUR")
        print("=" * 80 + "\n")

