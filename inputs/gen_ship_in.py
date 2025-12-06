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

        "capex": {
            "powertrain_type": "diesel",
            "vehicle_number": 1,
            "vehicle_id": 1,
            "vehicle_weight_class": "light",
            "country": "FR",
            "year": 2025,

            # Vehicle acquisition
            "is_new": True,
            "owns_vehicle": False,
            "purchase_price": 50000.0,
            "conversion_cost": 0.0,
            "certification_cost": 0.0,

            # Infrastructure
            "n_slow": None,
            "n_fast": None,
            "n_ultra": None,
            "n_stations": 1,
            "smart_charging_enabled": False,

            # Financing
            "loan_years": 10,

            # Vehicle charging / energy structure (ONLY place where E_t, S_t, etc. are allowed)
            "vehicle_dict": {
                "1": {
                    "E_t": 0.0,
                    "S_t": 0.0,
                    "F_t": 0.0,
                    "U_t": 0.0,
                    "Public_t": 0.0,
                    "Private_t": 1.0
                }
            }
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

