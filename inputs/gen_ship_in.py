def make_example_ship_electric():
    """
    Example dictionary for an ELECTRIC SHIP (vessel).
    Battery electric ship with shore power charging infrastructure.
"""
    purchase_price = 3_500_000.0
    operation_years = 15
    annual_dist = 50_000.0 # Nautical miles
    
    return {
        "asset_type": "ship",
        "description": "Electric Ferry - Battery Electric with shore charging",

        # Common data
        "powertrain_type": "BEV",
        "vehicle_weight_class": "large",
        "country": "France",
        "year": 2025,
        "operation_years": operation_years,
        "discount_rate": 0.05,

        # ---------- CAPEX ----------
        "capex": {
            "powertrain_type": "BEV",
            "vehicle_number": 1,
            "purchase_price": purchase_price,
            "is_new": True,
            "owns_vehicle": True,
            "n_slow": 1,   # 25 kW
            "n_fast": 2,   # 100 kW
            "n_ultra": 1,  # 300 kW
            "smart_charging_enabled": True,
            "loan_years": 15,
            "vehicle_dict": {
                "1": {
                    "E_t": 2_500_000.0,  # Annual kWh needed
                    "Private_S_t": 0.30, 
                    "Private_F_t": 0.50,
                    "Private_U_t": 0.20,
                }
            }
        },

        # ---------- OPEX SHIP ----------
        "opex_ship": {
            "purchase_price": purchase_price,
            "type_energy": "BEV",
            "annual_distance_travel": annual_dist,
            "consumption_energy": 2_500_000.0, # Total Annual kWh
            "crew_count": 12,
            "maintenance_cost": 45_000.0, # Annual estimated
            "fuel_multiplier": 1.0,
            "EF_CO2_fuel": 0.0, # Zero direct emissions
            "GT": 500.0,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "ship",
            "type_energy": "BEV",
            "registration_country": "France",
            "purchase_cost": 3_500_000.0,
            "year_purchase": 2025,
            "current_year": 2040,  # 15 years later
            "travel_measure": 750_000.0,  # nautical miles
            "maintenance_cost": 250_000.0,
            "minimum_fuel_consumption": 500.0,  # kWh/nm
            "powertrain_model_year": 2025,
            "warranty": 7.0,
            "type_warranty": 'year',
            "energy_price": 0.45,  # €/kWh for shore power
            "co2_taxes": 0.0,
            "subsidies": 350_000.0,  # Government subsidy for green shipping
            "vehicle_number": 1,
        },
    }


def make_example_ship_diesel():
    """
    Refined dictionary for a DIESEL SHIP (vessel).
    Traditional diesel-powered cargo ship with CO2 tax considerations.
    """
    purchase_price = 2_000_000.0
    operation_years = 15
    annual_dist = 60_000.0
    
    return {
        "asset_type": "ship",
        "description": "Medium Diesel Cargo Ship",

        # Common data
        "powertrain_type": "DIESEL",
        "vehicle_weight_class": "medium",
        "country": "France",
        "year": 2025,
        "operation_years": operation_years,
        "discount_rate": 0.045,

        # ---------- CAPEX ----------
        "capex": {
            "powertrain_type": "DIESEL",
            "vehicle_number": 1,
            "purchase_price": purchase_price,
            "is_new": True,
            "n_stations": 1, # Fuel tank/bunkering system
            "loan_years": 15,
            "vehicle_dict": {
                "1": {
                    "E_t": 1_825_000.0, # Liter/year (5000/day * 365)
                    "Private_t": 1.0,
                }
            }
        },

        # ---------- OPEX SHIP ----------
        "opex_ship": {
            "purchase_price": purchase_price,
            "type_energy": "DIESEL",
            "annual_distance_travel": annual_dist,
            "crew_count": 8,
            "maintenance_cost": 80_000.0, # Higher maintenance for internal combustion
            "consumption_energy": 1_825_000.0, # Liters
            "fuel_multiplier": 1.0,
            "EF_CO2_fuel": 2.65, # kg CO2 per liter
            "GT": 5000.0,
        },

        # ---------- RV ----------
        "rv": {
            "type_vehicle": "ship",
            "type_energy": "DIESEL",
            "registration_country": "France",
            "purchase_cost": 2_000_000.0,
            "year_purchase": 2025,
            "current_year": 2040,
            "travel_measure": 900_000.0,
            "maintenance_cost": 400_000.0,
            "minimum_fuel_consumption": 800.0,
            "powertrain_model_year": 2025,
            "warranty": 5.0,
            "type_warranty": 'year',
            "energy_price": 0.65,  # €/liter marine diesel
            "co2_taxes": 0.045,
            "subsidies": 0.0,
            "vehicle_number": 1,
        },
    }