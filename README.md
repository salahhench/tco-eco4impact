# CAPEX - CAPITAL EXPENDITURE

## Summary

This project is designed to calculate the **Capital Expenditure (CAPEX)** of vehicles, considering acquisition costs, infrastructure investments, taxes, financing, and subsidies. It is built using the `cosapp` library, which provides a framework for creating and connecting systems.

The CAPEX calculator follows the same architectural pattern as the OPEX system, ensuring consistency and maintainability across the TCO (Total Cost of Ownership) project.

---

##  File Structure

### `capex_calculator.py`

This file contains the core logic for the CAPEX calculation. It is structured as a `cosapp` system, which allows for modular and extensible design.

**Key Components:**

- **`VehicleCAPEXPort`**: This is a `cosapp` Port that defines all input data (ORANGE arrows) and output results (GREEN arrows) for the calculation. It includes:
    - Vehicle characteristics (powertrain type, weight class, purchase price)
    - Energy consumption patterns (E_t, S_t, F_t, U_t for charging distribution)
    - Infrastructure parameters (number of chargers/stations)
    - Financing parameters (loan years, interest rates)

- **`VehicleCAPEXCalculator`**: This is the main `cosapp` System. It takes data from the input port and calculates CAPEX through a series of modular steps:
    
    1. **Vehicle Cost** (`compute_c_vehicle_cost`):
        - Purchase price for new vehicles
        - Conversion + certification costs for retrofitted vehicles
        - Handles both new purchases and vehicle conversions
    
    2. **Infrastructure Cost** (`compute_c_infrastructure_cost`):
        - **For Electric Vehicles (BET/PHEV)**:
            - Hardware: Slow/Fast/Ultra-fast chargers
            - Grid connection based on total power requirements
            - Installation costs per charger type
        - **For Fuel Vehicles (Diesel/H2/GNV/LNG)**:
            - Fueling station hardware
            - Grid/electricity connections
            - Installation per station
        - **Common costs**:
            - Software (charge management, monitoring)
            - Site preparation
            - Safety equipment
            - Licensing fees
    
    3. **Taxes** (`compute_c_taxes`):
        - Registration taxes based on country, vehicle class, and powertrain type
        - Retrieved from database per jurisdiction
    
    4. **Subsidies** (`compute_c_subsidies`):
        - Vehicle subsidies (threshold-based or fixed)
        - Infrastructure subsidies (percentage of infrastructure cost)
        - Country and year-specific incentive programs
    
    5. **Financing Cost** (`compute_c_financing_cost`):
        - Origination fees
        - ESG adjustments (green financing discounts)
        - **CRF (Capital Recovery Factor)**: Annualizes the CAPEX investment        CRF = [r(1+r)^n] / [(1+r)^n - 1]