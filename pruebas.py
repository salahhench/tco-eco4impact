"""
Test script for Residual Value Calculator
"""

from main import ResidualValueCalculator
from cosapp.drivers import RunOnce
from datetime import datetime

def print_results(system, scenario_name):
    """Print formatted results"""
    print("\n" + "="*80)
    print(f"SCENARIO: {scenario_name}")
    print("="*80)
    print(f"\nVehicle: {system.in_vehicle_properties.type_energy.upper()} {system.in_vehicle_properties.type_vehicle}")
    print(f"Country: {system.in_vehicle_properties.registration_country}")
    print(f"Purchase Cost: ${system.in_vehicle_properties.purchase_cost:,.2f}")
    print(f"Vehicle Age: {system.in_vehicle_properties.current_year - system.in_vehicle_properties.year_purchase} years")
    print(f"Travel: {system.in_vehicle_properties.travel_measure:,.0f} km")
    
    print("\n" + "-"*80)
    print("DEPRECIATION")
    print("-"*80)
    print(f"Total Depreciation Value: ${system.total_depreciation:,.2f}")
    
    print("\n" + "-"*80)
    print("IMPACT HEALTH PENALTIES")
    print("-"*80)
    print(f"  • Efficiency Penalty:     {system.efficiency_penalty:.2f}%")
    print(f"  • Obsolescence Penalty:   {system.obsolescence_penalty:.2f}%")
    print(f"  • Charging Penalty:       {system.charging_penalty:.2f}%")
    print(f"  • Warranty Penalty:       {system.warranty_penalty:.2f}%")
    print(f"  Total Impact Health:      ${system.total_impact_health:,.2f}")
    
    print("\n" + "-"*80)
    print("EXTERNAL FACTORS")
    print("-"*80)
    print(f"External Factors Adjustment: ${system.total_external_factors:,.2f}")
    
    print("\n" + "="*80)
    print(f"FINAL RESIDUAL VALUE: ${system.rv:,.2f}")
    print("="*80)


def scenario_1_diesel_truck():
    """Scenario 1: Diesel truck in France"""
    rv_calc = ResidualValueCalculator(db_path='database_rv.json')
    
    # Vehicle properties
    rv_calc.in_vehicle_properties.type_vehicle = 'truck'
    rv_calc.in_vehicle_properties.type_energy = 'diesel'
    rv_calc.in_vehicle_properties.registration_country = 'France'
    rv_calc.in_vehicle_properties.purchase_cost = 80000.0
    rv_calc.in_vehicle_properties.year_purchase = 2020
    rv_calc.in_vehicle_properties.current_year = 2024
    rv_calc.in_vehicle_properties.travel_measure = 150000.0  # km
    rv_calc.in_vehicle_properties.maintenance_cost = 8000.0
    rv_calc.in_vehicle_properties.minimum_fuel_consumption = 250.0  # g/kWh
    rv_calc.in_vehicle_properties.powertrain_model_year = 2020
    rv_calc.in_vehicle_properties.warranty = 5.0
    rv_calc.in_vehicle_properties.type_warranty = 'years'
    
    # Country properties
    rv_calc.in_country_properties.energy_price = 1.5  # $/L
    rv_calc.in_country_properties.c02_taxes = 500.0
    rv_calc.in_country_properties.subsidies = 0.0
    
    # Run calculation
    driver = RunOnce()
    driver.set_scenario(rv_calc)
    driver.run()
    
    print_results(rv_calc, "Diesel Truck in France (4 years old)")


def scenario_2_electric_truck():
    """Scenario 2: Electric truck in Germany"""
    rv_calc = ResidualValueCalculator(db_path='database_rv.json')
    
    # Vehicle properties
    rv_calc.in_vehicle_properties.type_vehicle = 'truck'
    rv_calc.in_vehicle_properties.type_energy = 'electric'
    rv_calc.in_vehicle_properties.registration_country = 'Germany'
    rv_calc.in_vehicle_properties.purchase_cost = 150000.0
    rv_calc.in_vehicle_properties.year_purchase = 2022
    rv_calc.in_vehicle_properties.current_year = 2024
    rv_calc.in_vehicle_properties.travel_measure = 50000.0  # km
    rv_calc.in_vehicle_properties.maintenance_cost = 3000.0
    rv_calc.in_vehicle_properties.consumption_real = 1.2  # kWh/km
    rv_calc.in_vehicle_properties.powertrain_model_year = 2022
    
    # Battery and charging info
    rv_calc.in_vehicle_properties.E_annual_kwh = 30000.0
    rv_calc.in_vehicle_properties.C_bat_kwh = 300.0
    rv_calc.in_vehicle_properties.DoD = 0.8
    rv_calc.in_vehicle_properties.S_slow = 0.6
    rv_calc.in_vehicle_properties.S_fast = 0.3
    rv_calc.in_vehicle_properties.S_ultra = 0.1
    
    rv_calc.in_vehicle_properties.warranty = 8.0
    rv_calc.in_vehicle_properties.type_warranty = 'years'
    
    # Country properties
    rv_calc.in_country_properties.energy_price = 0.3  # $/kWh
    rv_calc.in_country_properties.c02_taxes = 0.0
    rv_calc.in_country_properties.subsidies = 1.0  # Multiplier for subsidy
    
    # Run calculation
    driver = RunOnce()
    driver.set_scenario(rv_calc)
    driver.run()
    
    print_results(rv_calc, "Electric Truck in Germany (2 years old)")


def scenario_3_hybrid_truck():
    """Scenario 3: Hybrid truck in France"""
    rv_calc = ResidualValueCalculator(db_path='database_rv.json')
    
    # Vehicle properties
    rv_calc.in_vehicle_properties.type_vehicle = 'truck'
    rv_calc.in_vehicle_properties.type_energy = 'hybrid'
    rv_calc.in_vehicle_properties.registration_country = 'France'
    rv_calc.in_vehicle_properties.purchase_cost = 120000.0
    rv_calc.in_vehicle_properties.year_purchase = 2021
    rv_calc.in_vehicle_properties.current_year = 2024
    rv_calc.in_vehicle_properties.travel_measure = 100000.0  # km
    rv_calc.in_vehicle_properties.maintenance_cost = 5000.0
    rv_calc.in_vehicle_properties.utility_factor = 0.4  # 40% electric usage
    rv_calc.in_vehicle_properties.powertrain_model_year = 2021
    rv_calc.in_vehicle_properties.warranty = 6.0
    rv_calc.in_vehicle_properties.type_warranty = 'years'
    
    # Country properties
    rv_calc.in_country_properties.energy_price = 1.5  # $/L
    rv_calc.in_country_properties.c02_taxes = 300.0
    rv_calc.in_country_properties.subsidies = 1.0
    
    # Run calculation
    driver = RunOnce()
    driver.set_scenario(rv_calc)
    driver.run()
    
    print_results(rv_calc, "Hybrid Truck in France (3 years old)")


def scenario_4_hydrogen_truck():
    """Scenario 4: Hydrogen fuel cell truck in Germany"""
    rv_calc = ResidualValueCalculator(db_path='database_rv.json')
    
    # Vehicle properties
    rv_calc.in_vehicle_properties.type_vehicle = 'truck'
    rv_calc.in_vehicle_properties.type_energy = 'hydrogen_fuel_cell'
    rv_calc.in_vehicle_properties.registration_country = 'Germany'
    rv_calc.in_vehicle_properties.purchase_cost = 200000.0
    rv_calc.in_vehicle_properties.year_purchase = 2023
    rv_calc.in_vehicle_properties.current_year = 2024
    rv_calc.in_vehicle_properties.travel_measure = 25000.0  # km
    rv_calc.in_vehicle_properties.maintenance_cost = 2000.0
    rv_calc.in_vehicle_properties.consumption_real = 8.0  # kg/100km
    rv_calc.in_vehicle_properties.powertrain_model_year = 2023
    rv_calc.in_vehicle_properties.warranty = 10.0
    rv_calc.in_vehicle_properties.type_warranty = 'years'
    
    # Country properties
    rv_calc.in_country_properties.energy_price = 12.0  # $/kg
    rv_calc.in_country_properties.c02_taxes = 0.0
    rv_calc.in_country_properties.subsidies = 1.0
    
    # Run calculation
    driver = RunOnce()
    driver.set_scenario(rv_calc)
    driver.run()
    
    print_results(rv_calc, "Hydrogen Fuel Cell Truck in Germany (1 year old)")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("RESIDUAL VALUE CALCULATOR - TEST SCENARIOS")
    print("="*80)
    
    # Run all scenarios
    scenario_1_diesel_truck()
    scenario_2_electric_truck()
    scenario_3_hybrid_truck()
    scenario_4_hydrogen_truck()
    
    print("\n" + "="*80)
    print("ALL SCENARIOS COMPLETED")
    print("="*80 + "\n")