# %%%

"""
Residual Value (RV) Calculator for Trucks and Ships
"""
# %%
import numpy as np
from cosapp.base import System
from enum import Enum


class EnergyType(Enum):
    """Allowed energy types for vehicles"""
    DIESEL_FOSILE = "Diesel_fosile"
    EDIESEL = "eDiesel"
    GNV = "GNV"
    H2_ICE = "H2-ICE"
    BET = "BET"
    FCET = "FCET"
    HEV = "HEV"
    PHEV = "PHEV"

class VehicleType(Enum):
    """Vehicle types"""
    TRUCK = "Truck"
    SHIP = "Ship"

# %% ==================== SUB-MODULE 1: DEPRECIATION ====================
class DepreciationSystem(System):
    """
    Calculates vehicle depreciation based on age, usage, and maintenance costs.
    """
    
    def setup(self):
        # Inputs from user
        self.add_inward("purchase_cost", 100000.0, desc="Initial acquisition cost (€)")
        self.add_inward("age_vehicle", 5.0, desc="Age of vehicle (years)")
        self.add_inward("travel_measure", 200000.0, desc="Distance (km) or hours (h)")
        self.add_inward("maintenance_cost", 15000.0, desc="Cumulative maintenance cost (€)")
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        
        # Parameters from database
        self.add_inward("depreciation_rate_per_year", 5000.0, desc="Annual depreciation (€/year)")
        self.add_inward("depreciation_rate_by_usage", 0.05, desc="Depreciation per km (€/km)")
        self.add_inward("coef_depreciation_maintenance", 0.10, desc="Maintenance impact coefficient")
        
        # Output
        self.add_outward("depreciation", 0.0, desc="Total depreciation value (€)")
    
    def compute(self):
        # Calculate depreciation components
        depreciation_per_year = self.depreciation_rate_per_year * self.age_vehicle
        depreciation_by_usage = self.depreciation_rate_by_usage * self.travel_measure
        depreciation_due_to_maintenance = self.coef_depreciation_maintenance * self.maintenance_cost
        
        # Total depreciation
        self.depreciation = (self.purchase_cost - 
                           depreciation_per_year - 
                           depreciation_by_usage - 
                           depreciation_due_to_maintenance)
        
        # Ensure depreciation doesn't go below zero
        self.depreciation = max(0.0, self.depreciation)


# %% ==================== SUB-MODULE 2: TECH (Fuel Conversion Efficiency) ====================
class TechSystem(System):
    """
    Calculates fuel conversion efficiency penalty.
    """
    
    def setup(self):
        # Inputs
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        self.add_inward("minimum_fuel_consumption", 200.0, desc="SFC (g/kWh)")
        self.add_inward("consumption_real", 0.0, desc="Real consumption (kWh/km or kg/100km)")
        self.add_inward("utility_factor", 0.5, desc="Electric fraction for hybrids")
        
        # Parameters from database
        self.add_inward("consumption_benchmark", 0.0, desc="Benchmark consumption")
        self.add_inward("heating_value", 42.6, desc="Q_HV Lower heating value (MJ/kg)")
        self.add_inward("n_EV", 0.85, desc="Electric propulsion efficiency")
        self.add_inward("n_ICE", 0.40, desc="ICE efficiency")
        
        # Output
        self.add_outward("tech_penalty", 0.0, desc="Technology inefficiency penalty (%)")
    
    def compute(self):
        n = 0.0
        
        # A) Diesel, H2-ICE
        if self.type_energy in ["Diesel_fosile", "eDiesel", "H2-ICE"]:
            n = 3600.0 / (self.minimum_fuel_consumption * self.heating_value)
        
        # B) BET, FCET
        elif self.type_energy in ["BET", "FCET"]:
            if self.consumption_real > 0:
                n = self.consumption_benchmark / self.consumption_real
            else:
                n = 0.85  # Default assumption
        
        # C) HEV/PHEV
        elif self.type_energy in ["HEV", "PHEV"]:
            alpha = self.utility_factor
            denominator = (alpha / self.n_EV) + ((1 - alpha) / self.n_ICE)
            n = 1.0 / denominator if denominator > 0 else 0.0
        
        # Technology penalty: tech() = (1 - η) * 100%
        self.tech_penalty = (1.0 - n) * 100.0
        self.tech_penalty = max(0.0, min(100.0, self.tech_penalty))


# ==================== SUB-MODULE 3: QUALITY FUEL ====================
class QualityFuelSystem(System):
    """
    Calculates fuel quality factor penalty.
    CRITICAL: Only applies to fuel-based energy types. BET/FCET must return 0.
    """
    
    def setup(self):
        # Inputs
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        
        # Parameters from database
        self.add_inward("LHV", 42.6, desc="Lower heating value actual fuel (MJ/kg)")
        self.add_inward("density", 835.0, desc="Density actual fuel (kg/m³)")
        self.add_inward("LHV_ref", 43.0, desc="Reference LHV (MJ/kg)")
        self.add_inward("density_ref", 840.0, desc="Reference density (kg/m³)")
        
        # Output
        self.add_outward("type_penalty", 0.0, desc="Fuel quality penalty")
    
    def compute(self):
        # CRITICAL CONSTRAINT: Only calculate for fuel-based types
        fuel_based_types = ["Diesel_fosile", "eDiesel", "GNV", "H2-ICE", "HEV", "PHEV"]
        
        if self.type_energy in fuel_based_types:
            # Calculate DF factor
            DF = (self.LHV * self.density) / (self.LHV_ref * self.density_ref)
            
            # Penalty: deviation from ideal (DF = 1)
            self.type_penalty = abs(1.0 - DF) * 100.0
        else:
            # BET and FCET: penalty must be 0
            self.type_penalty = 0.0


# ==================== SUB-MODULE 4: OBSOLESCENCE (POWER MODEL) ====================
class ObsolescenceSystem(System):
    """
    Calculates powertrain model obsolescence factor.
    """
    
    def setup(self):
        # Inputs
        self.add_inward("powertrain_model_year", 2020, desc="Powertrain model year")
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        self.add_inward("distance_travel", 100000.0, desc="Distance travelled (km)")
        self.add_inward("current_year", 2024, desc="Current year")
        
        # Parameters from database
        self.add_inward("lambda_y", 0.05, desc="Yearly obsolescence rate (1/year)")
        self.add_inward("lambda_d", 0.00001, desc="Distance obsolescence rate (1/km)")
        self.add_inward("inicial_distance", 0.0, desc="Initial distance")
        
        # Output
        self.add_outward("obsolence_penalty", 0.0, desc="Obsolescence penalty")
    
    def compute(self):
        DM = 1.0
        
        # Time-based obsolescence (trucks)
        if self.type_vehicle == "Truck":
            years_diff = self.current_year - self.powertrain_model_year
            DM = np.exp(-self.lambda_y * years_diff)
        
        # Distance-based obsolescence (ships)
        elif self.type_vehicle == "Ship":
            distance_diff = self.distance_travel - self.inicial_distance
            DM = np.exp(-self.lambda_d * distance_diff)
        
        # Penalization: RISK = 1 - DM
        self.obsolence_penalty = (1.0 - DM) * 100.0
        self.obsolence_penalty = max(0.0, min(100.0, self.obsolence_penalty))


# ==================== SUB-MODULE 5: WARRANTY ====================
class WarrantySystem(System):
    """
    Calculates warranty factor penalty.
    Section 5.2.4 of Report 1
    """
    
    def setup(self):
        # Inputs
        self.add_inward("warranty", 2.0, desc="Warranty duration (years or km)")
        self.add_inward("type_warranty", "years", desc="Type of warranty")
        self.add_inward("year_purchase", 2020, desc="Year of purchase")
        self.add_inward("current_year", 2024, desc="Current year")
        
        # Output
        self.add_outward("warranty_penalty", 0.0, desc="Warranty expiration penalty")
    
    def compute(self):
        # Calculate elapsed time
        elapsed = self.current_year - self.year_purchase
        
        # Calculate DW factor (limited to [0, 1])
        if self.warranty > 0:
            DW = 1.0 - (elapsed / self.warranty)
            DW = max(0.0, min(1.0, DW))
        else:
            DW = 0.0
        
        # Penalization: RISK_W = 1 - DW
        self.warranty_penalty = (1.0 - DW) * 100.0


# ==================== SUB-MODULE 6: CHARGING ====================
class ChargingSystem(System):
    """
    Calculates battery charging degradation penalty.
    CRITICAL: Only applies to BET (Battery Electric Trucks). All other types must return 0.
    """
    
    def setup(self):
        # Inputs
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        self.add_inward("E_annual_kwh", 50000.0, desc="Annual energy consumption (kWh)")
        self.add_inward("C_bat_kwh", 300.0, desc="Battery capacity (kWh)")
        self.add_inward("DoD", 0.80, desc="Depth of discharge")
        self.add_inward("S_slow", 0.60, desc="Proportion slow charging")
        self.add_inward("S_fast", 0.30, desc="Proportion fast charging")
        self.add_inward("S_ultra", 0.10, desc="Proportion ultra-fast charging")
        
        # Parameters from database
        self.add_inward("d_slow", 1.0, desc="Degradation factor slow")
        self.add_inward("d_fast", 1.5, desc="Degradation factor fast")
        self.add_inward("d_ultra", 2.5, desc="Degradation factor ultra")
        self.add_inward("k_d", 0.001, desc="Global scaling coefficient")
        
        # Output
        self.add_outward("charging_penalty", 0.0, desc="Charging degradation penalty")
    
    def compute(self):
        # CRITICAL CONSTRAINT: Only calculate for BET
        if self.type_energy == "BET":
            # Average degradation per cycle
            degradation_per_cycle = (self.S_slow * self.d_slow + 
                                   self.S_fast * self.d_fast + 
                                   self.S_ultra * self.d_ultra)
            
            # Equivalent full cycles per year
            if self.C_bat_kwh > 0 and self.DoD > 0:
                cycles = self.E_annual_kwh / (self.C_bat_kwh * self.DoD)
            else:
                cycles = 0.0
            
            # Total annual degradation
            D = cycles * degradation_per_cycle
            
            # Charging health factor (exponential decay)
            health_charging = np.exp(-self.k_d * D)
            
            # Penalization: charging = 1 - health_charging
            self.charging_penalty = (1.0 - health_charging) * 100.0
            self.charging_penalty = max(0.0, min(100.0, self.charging_penalty))
        else:
            # All non-BET types: penalty must be 0
            self.charging_penalty = 0.0

# %% ==================== AGGREGATION: IMPACT OF HEALTH POWERTRAIN ====================
class ImpactHealthSystem(System):
    """
    Aggregates all powertrain health penalties.
    Parent system containing: tech, quality_fuel, obsolescence, warranty, charging
    """
    
    def setup(self):
        # Add child systems
        self.add_child(TechSystem("tech"))
        self.add_child(QualityFuelSystem("quality"))
        self.add_child(ObsolescenceSystem("obsolescence"))
        self.add_child(WarrantySystem("warranty"))
        self.add_child(ChargingSystem("charging"))
        
        # Common inputs
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        
        # Output
        self.add_outward("impact_health", 0.0, desc="Total health impact penalty")
    
    def compute(self):
        # Connect inputs to child systems
        for child_name in ["tech", "quality", "obsolescence", "charging"]:
            child = self[child_name]
            child.type_vehicle = self.type_vehicle
            child.type_energy = self.type_energy
        
        # Sum all penalties
        self.impact_health = (
            self.tech.tech_penalty +
            self.quality.type_penalty +
            self.obsolescence.obsolence_penalty +
            self.warranty.warranty_penalty +
            self.charging.charging_penalty
        )

# %% ==================== ROOT SYSTEM: RESIDUAL VALUE ====================
class ResidualValueSystem(System):
    """
    Root system calculating Residual Value (RV).
    Formula: RV = DEPRECIATION / IMPACT_OF_HEALTH_POWERTRAIN + TAXES
    """
    
    def setup(self):
        # Add child systems
        self.add_child(DepreciationSystem("depreciation_module"))
        self.add_child(ImpactHealthSystem("health_module"))
        
        # Common inputs
        self.add_inward("type_vehicle", "Truck", desc="Vehicle type")
        self.add_inward("type_energy", "Diesel_fosile", desc="Energy type")
        self.add_inward("taxes", 5000.0, desc="Tax value (€)")
        
        # Output
        self.add_outward("residual_value", 0.0, desc="Residual Value (€)")
    
    def compute(self):
        # Connect common inputs
        self.depreciation_module.type_vehicle = self.type_vehicle
        self.depreciation_module.type_energy = self.type_energy
        
        self.health_module.type_vehicle = self.type_vehicle
        self.health_module.type_energy = self.type_energy
        
        # Calculate RV
        depreciation = self.depreciation_module.depreciation
        impact_health = self.health_module.impact_health
        
        # Avoid division by zero
        if impact_health > 0:
            self.residual_value = (depreciation / (impact_health/100)) + self.taxes
        else:
            self.residual_value = depreciation + self.taxes

# %% ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    print("=" * 70)
    print("RESIDUAL VALUE (RV) CALCULATOR - CoSApp Implementation")
    print("=" * 70)
    
    # ==================== TEST CASE 1: Battery Electric Truck (BET) ====================
    print("\n" + "=" * 70)
    print("TEST CASE 1: Battery Electric Truck (BET)")
    print("=" * 70)
    
    rv_system_bet = ResidualValueSystem("rv_bet")
    
    # Set inputs for BET
    rv_system_bet.type_vehicle = "Truck"
    rv_system_bet.type_energy = "BET"
    rv_system_bet.taxes = 3000.0
    
    # Depreciation parameters
    rv_system_bet.depreciation_module.purchase_cost = 150000.0
    rv_system_bet.depreciation_module.age_vehicle = 3.0
    rv_system_bet.depreciation_module.travel_measure = 150000.0

    rv_system_bet.depreciation_module.maintenance_cost = 5000.0
    rv_system_bet.depreciation_module.depreciation_rate_per_year = 5000.0
    rv_system_bet.depreciation_module.depreciation_rate_by_usage = 0.5
    rv_system_bet.depreciation_module.coef_depreciation_maintenance = 1.2
    
    # Tech parameters (BET)
    rv_system_bet.health_module.tech.consumption_real = 1.2
    rv_system_bet.health_module.tech.consumption_benchmark = 1.0
    
    # Quality fuel (should be 0 for BET)
    # No parameters needed - will automatically return 0
    
    # Obsolescence
    rv_system_bet.health_module.obsolescence.powertrain_model_year = 2020
    rv_system_bet.health_module.obsolescence.current_year = 2024
    rv_system_bet.health_module.obsolescence.lambda_y = 0.05
    
    # Warranty
    rv_system_bet.health_module.warranty.warranty = 8.0
    rv_system_bet.health_module.warranty.year_purchase = 2022
    rv_system_bet.health_module.warranty.current_year = 2025
    
    # Charging (only applies to BET)
    rv_system_bet.health_module.charging.E_annual_kwh = 60000.0
    rv_system_bet.health_module.charging.C_bat_kwh = 400.0
    rv_system_bet.health_module.charging.DoD = 0.85
    rv_system_bet.health_module.charging.S_slow = 0.50
    rv_system_bet.health_module.charging.S_fast = 0.35
    rv_system_bet.health_module.charging.S_ultra = 0.15
    rv_system_bet.health_module.charging.d_slow = 1.0
    rv_system_bet.health_module.charging.d_fast = 1.8
    rv_system_bet.health_module.charging.d_ultra = 3.0
    rv_system_bet.health_module.charging.k_d = 0.0015
    
    # Run computation
    rv_system_bet.run_drivers()
    
    # Display results
    print(f"\nDEPRECIATION: €{rv_system_bet.depreciation_module.depreciation:,.2f}")
    print(f"\nHEALTH IMPACT BREAKDOWN:")
    print(f"  - Tech Penalty:         {rv_system_bet.health_module.tech.tech_penalty:.2f}%")
    print(f"  - Quality Fuel Penalty: {rv_system_bet.health_module.quality.type_penalty:.2f}% (Should be 0 for BET)")
    print(f"  - Obsolescence Penalty: {rv_system_bet.health_module.obsolescence.obsolence_penalty:.2f}%")
    print(f"  - Warranty Penalty:     {rv_system_bet.health_module.warranty.warranty_penalty:.2f}%")
    print(f"  - Charging Penalty:     {rv_system_bet.health_module.charging.charging_penalty:.2f}% (Only for BET)")
    print(f"\nTOTAL IMPACT_HEALTH: {rv_system_bet.health_module.impact_health:.2f}%")
    print(f"TAXES: €{rv_system_bet.taxes:,.2f}")
    print(f"\n{'*' * 70}")
    print(f"RESIDUAL VALUE (RV): €{rv_system_bet.residual_value:,.2f}")
    print(f"{'*' * 70}")
    
#     # ==================== TEST CASE 2: Diesel Truck ====================
#     print("\n\n" + "=" * 70)
#     print("TEST CASE 2: Diesel Fossil Truck")
#     print("=" * 70)
    
#     rv_system_diesel = ResidualValueSystem("rv_diesel")
    
#     # Set inputs for Diesel
#     rv_system_diesel.type_vehicle = "Truck"
#     rv_system_diesel.type_energy = "Diesel_fosile"
#     rv_system_diesel.taxes = 2500.0
    
#     # Depreciation parameters
#     rv_system_diesel.depreciation_module.purchase_cost = 120000.0
#     rv_system_diesel.depreciation_module.age_vehicle = 5.0
#     rv_system_diesel.depreciation_module.travel_measure = 250000.0
#     rv_system_diesel.depreciation_module.maintenance_cost = 18000.0
#     rv_system_diesel.depreciation_module.depreciation_rate_per_year = 4500.0
#     rv_system_diesel.depreciation_module.depreciation_rate_by_usage = 0.06
#     rv_system_diesel.depreciation_module.coef_depreciation_maintenance = 0.12
    
#     # Tech parameters (Diesel)
#     rv_system_diesel.health_module.tech.minimum_fuel_consumption = 210.0
#     rv_system_diesel.health_module.tech.heating_value = 42.6
    
#     # Quality fuel (applies to Diesel)
#     rv_system_diesel.health_module.quality.LHV = 42.0
#     rv_system_diesel.health_module.quality.density = 830.0
#     rv_system_diesel.health_module.quality.LHV_ref = 43.0
#     rv_system_diesel.health_module.quality.density_ref = 840.0
    
#     # Obsolescence
#     rv_system_diesel.health_module.obsolescence.powertrain_model_year = 2018
#     rv_system_diesel.health_module.obsolescence.current_year = 2025
#     rv_system_diesel.health_module.obsolescence.lambda_y = 0.06
    
#     # Warranty
#     rv_system_diesel.health_module.warranty.warranty = 5.0
#     rv_system_diesel.health_module.warranty.year_purchase = 2020
#     rv_system_diesel.health_module.warranty.current_year = 2025
    
#     # Charging (should be 0 for Diesel)
#     # No parameters needed - will automatically return 0
    
#     # Run computation
#     rv_system_diesel.run_drivers()
    
#     # Display results
#     print(f"\nDEPRECIATION: €{rv_system_diesel.depreciation_module.depreciation:,.2f}")
#     print(f"\nHEALTH IMPACT BREAKDOWN:")
#     print(f"  - Tech Penalty:         {rv_system_diesel.health_module.tech.tech_penalty:.2f}%")
#     print(f"  - Quality Fuel Penalty: {rv_system_diesel.health_module.quality.type_penalty:.2f}% (Applies to Diesel)")
#     print(f"  - Obsolescence Penalty: {rv_system_diesel.health_module.obsolescence.obsolence_penalty:.2f}%")
#     print(f"  - Warranty Penalty:     {rv_system_diesel.health_module.warranty.warranty_penalty:.2f}%")
#     print(f"  - Charging Penalty:     {rv_system_diesel.health_module.charging.charging_penalty:.2f}% (Should be 0 for Diesel)")
#     print(f"\nTOTAL IMPACT_HEALTH: {rv_system_diesel.health_module.impact_health:.2f}%")
#     print(f"TAXES: €{rv_system_diesel.taxes:,.2f}")
#     print(f"\n{'*' * 70}")
#     print(f"RESIDUAL VALUE (RV): €{rv_system_diesel.residual_value:,.2f}")
#     print(f"{'*' * 70}")
    
#     print("\n" + "=" * 70)
#     print("VERIFICATION OF CRITICAL CONSTRAINTS:")
#     print("=" * 70)
#     print(f"✓ BET charging penalty: {rv_system_bet.health_module.charging.charging_penalty:.2f}% (> 0, as expected)")
#     print(f"✓ BET quality fuel penalty: {rv_system_bet.health_module.quality.type_penalty:.2f}% (= 0, as required)")
#     print(f"✓ Diesel charging penalty: {rv_system_diesel.health_module.charging.charging_penalty:.2f}% (= 0, as required)")
#     print(f"✓ Diesel quality fuel penalty: {rv_system_diesel.health_module.quality.type_penalty:.2f}% (> 0, as expected)")
#     print("=" * 70)
# # %%

# %%
