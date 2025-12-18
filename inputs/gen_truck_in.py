"""
Example input scenarios for TCO calculations.
Contains configurations for both truck and ship scenarios.
"""


def make_example_truck_electric_fleet():
    """
    Example dictionary for an ELECTRIC TRUCK FLEET.
    - 5 BET (Battery Electric Trucks) in the fleet
    - Multiple chargers: slow, fast, and ultra-fast
    - Heavy trucks operating in France
    """
    return {
        "asset_type": "truck",
        "description": "Electric Truck Fleet - 5 Heavy BET vehicles with mixed charging infrastructure",

        # Common data
        "powertrain_type": "BEV",
        "vehicle_weight_class": "heavy",
        "country": "France",
        "year": 2025,
        "operation_years": 10,
        "discount_rate": 0.045,  # 4.5% discount rate

        # ---------- CAPEX ----------
        "capex": {
            "powertrain_type": "BET",
            "vehicle_number": 5,
            "vehicle_id": 1,  # This calculation is for vehicle 1
            "vehicle_weight_class": "heavy",
            "country": "France",
            "year": 2025,

            # Vehicle acquisition
            "is_new": True,
            "owns_vehicle": False,
            "purchase_price": 180000.0,  # BET trucks are more expensive
            "conversion_cost": 0.0,
            "certification_cost": 0.0,

            # Infrastructure - Multiple chargers for fleet
            "n_slow": 3,   # 3 slow chargers (11 kW)
            "n_fast": 2,   # 2 fast chargers (50 kW)
            "n_ultra": 1,  # 1 ultra-fast charger (150 kW)
            "n_stations": None,  # Not needed for electric
            "smart_charging_enabled": True,  # Enable smart charging

            # Financing
            "loan_years": 10,

            # Fleet energy structure - 5 vehicles with different charging patterns
            "vehicle_dict": {
                "1": {
                    "E_t": 250.0,  # 250 kWh per day
                    "Private_S_t": 0.60,  # 60% slow charging
                    "Private_F_t": 0.30,  # 30% fast charging
                    "Private_U_t": 0.10,  # 10% ultra-fast charging
                },
                "2": {
                    "E_t": 280.0,
                    "Private_S_t": 0.50,
                    "Private_F_t": 0.40,
                    "Private_U_t": 0.10,
                },
                "3": {
                    "E_t": 230.0,
                    "Private_S_t": 0.70,
                    "Private_F_t": 0.20,
                    "Private_U_t": 0.10,
                },
                "4": {
                    "E_t": 260.0,
                    "Private_S_t": 0.55,
                    "Private_F_t": 0.35,
                    "Private_U_t": 0.10,
                },
                "5": {
                    "E_t": 240.0,
                    "Private_S_t": 0.65,
                    "Private_F_t": 0.25,
                    "Private_U_t": 0.10,
                }
            }
        },

        # ---------- OPEX TRUCK ----------
        "opex_truck": {
            "purchase_price": 180000.0,
            "type_energy": "BEV",
            "size_vehicle": "N3",
            "registration_country": "France",
            "annual_distance_travel": 80_000.0,  # Electric trucks have shorter range
            "departure_city": "Lyon",
            "arrival_city": "Bordeaux",
            "N_years": 10.0,
            "team_count": 1,
            "maintenance_cost": 0,
            "consumption_energy": 0,
            "fuel_multiplier": 1.0,
            "EF_CO2_diesel": 0.0,  # Zero direct emissions for BET
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "truck",
            "type_energy": "BEV",
            "registration_country": "France",
            "purchase_cost": 180000.0,
            "year_purchase": 2025,
            "current_year": 2035,  # 10 years later
            "travel_measure": 800_000.0,  # 80k km/year * 10 years
            "maintenance_cost": 15000.0,
            "minimum_fuel_consumption": 150.0,  # kWh/100km
            "powertrain_model_year": 2025,
            "warranty": 5.0,
            "type_warranty": 'year',
            "energy_price": 0.18,  # €/kWh electricity price
            "co2_taxes": 0.0,
            "subsidies": 5000.0,
            "vehicle_number": 5,
        },
    }


def make_example_truck_diesel():
    """
    Example dictionary for a DIESEL TRUCK (single vehicle).
    Traditional diesel truck for comparison.
    """
    return {
        "asset_type": "truck",
        "description": "Heavy diesel N3 truck in France",

        # Common data
        "powertrain_type": "DIESEL",
        "vehicle_weight_class": "heavy",
        "country": "France",
        "year": 2025,
        "operation_years": 10,
        "discount_rate": 0.04,  # 4% discount rate

        # ---------- CAPEX ----------
        "capex": {
            "powertrain_type": "DIESEL",
            "vehicle_number": 1,
            "vehicle_id": 1,
            "vehicle_weight_class": "heavy",
            "country": "France",
            "year": 2025,

            # Vehicle acquisition
            "is_new": True,
            "owns_vehicle": False,
            "purchase_price": 120000.0,
            "conversion_cost": 0.0,
            "certification_cost": 0.0,

            # Infrastructure
            "n_slow": None,
            "n_fast": None,
            "n_ultra": None,
            "n_stations": 1,  # One diesel station
            "smart_charging_enabled": False,

            # Financing
            "loan_years": 10,

            # Vehicle energy structure
            "vehicle_dict": {
                "1": {
                    "E_t": 400.0,  # Diesel consumption
                    "Private_t": 1.0,  # 100% private fueling
                }
            }
        },

        # ---------- OPEX TRUCK ----------
        "opex_truck": {
            "purchase_price": 120000.0,
            "type_energy": "DIESEL",
            "size_vehicle": "N3",
            "registration_country": "France",
            "annual_distance_travel": 120_000.0,
            "departure_city": "Paris",
            "arrival_city": "Marseille",
            "RV": 40_000.0,
            "N_years": 10.0,
            "team_count": 1,
            "maintenance_cost": 0,
            "consumption_energy": 0,
            "fuel_multiplier": 1.0,
            "EF_CO2_diesel": 2.65,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "truck",
            "type_energy": "DIESEL",
            "registration_country": "France",
            "purchase_cost": 120000.0,
            "year_purchase": 2025,
            "current_year": 2035,
            "travel_measure": 1_200_000.0,
            "maintenance_cost": 25000.0,
            "minimum_fuel_consumption": 300.0,
            "powertrain_model_year": 2025,
            "warranty": 3.0,
            "type_warranty": 'year',
            "energy_price": 1.65,  # €/liter diesel
            "co2_taxes": 0.045,
            "subsidies": 0.0,
            "vehicle_number": 1,
        },
    }


