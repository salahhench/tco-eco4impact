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


        # ---------- OPEX TRUCK ----------
        "opex_truck": {
            "purchase_cost": 155000.0,
            "type_energy": "diesel",
            "size_vehicle": "N3",
            "registration_country": "France",
            "annual_distance_travel": 120_000.0,
            "departure_city": "Paris",
            "arrival_city": "Marseille",
            "RV": 45_000.0,
            "N_years": 5.0,
            "team_count": 1,
            "maintenance_cost": 0,
            "consumption_energy": 0,
            "fuel_multiplier": 1.0,
            "EF_CO2_diesel": 2.65,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "truck",
            "type_energy": "diesel",
            "registration_country": "France",
            "purchase_cost": 155000.0,
            "year_purchase": 2025,
            "current_year": 2025,
            "travel_measure": 0,
            "maintenance_cost": 0,
            "minimum_fuel_consumption": 200,
            "powertrain_model_year" : 2023,
            "warranty" : 2,
            "type_warranty" : 'years',
            "energy_price": 1.5,
            "c02_taxes": 0,
            "subsidies":0,
            "vehicle_number": 1,
        },
    }

