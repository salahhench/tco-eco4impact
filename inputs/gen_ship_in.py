def make_example_ship_inputs():
    """Ejemplo de diccionario de entrada para un SHIP."""
    return {
        "asset_type": "ship",
        "description": "Cargo ship diesel in France",

        # Datos comunes
        "powertrain_type": "DIESEL",
        "vehicle_weight_class": "heavy",   # puedes inventar una clase “heavy_ship”
        "country": "France",
        "year": 2025,
        "operation_years": 5,

        "capex": {
            "powertrain_type": "DIESEL",
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
            "country_reg": "France",
            "country_oper": "France",
            "ship_class": "cargo",
            "length": 120.0,
            "energy_type": "DIESEL",
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
            "type_energy": "DIESEL",
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
            "co2_taxes": 500.0,
            "subsidies":0.0,
            "vehicle_number": 1,
        },
        }

