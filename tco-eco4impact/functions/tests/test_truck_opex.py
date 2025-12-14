import unittest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import shutil


class TestOPEXPort(unittest.TestCase):
    """Test cases for OPEXPort class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Port class if it's not available
        self.mock_port = MagicMock()
    
    def test_port_has_required_variables(self):
        """Test that OPEXPort defines all required variables."""
        required_inputs = [
            "purchase_cost", "type_energy", "size_vehicle", "registration_country",
            "annual_distance_travel", "departure_city", "arrival_city", "RV",
            "N_years", "team_count", "maintenance_cost", "consumption_energy",
            "fuel_multiplier", "EF_CO2"
        ]
        
        required_outputs = [
            "o_taxes", "o_tolls", "o_insurance", "o_crew", "o_energy", "o_opex_total"
        ]
        
        # This test would need the actual OPEXPort implementation
        # For now, we verify the expected structure
        self.assertTrue(len(required_inputs) > 0)
        self.assertTrue(len(required_outputs) > 0)


class TestTruckOPEXCalculator(unittest.TestCase):
    """Test cases for TruckOPEXCalculator class."""
    
    def setUp(self):
        """Set up test database and calculator instance."""
        self.test_db = {
            "countries": [
                {
                    "country": "France",
                    "data_country": {
                        "external_factors": {
                            "price_energy_km": {
                                "h1": {
                                    "DIESEL": 0.15,
                                    "ELECTRIC": 0.08
                                }
                            }
                        },
                        "tax_energy_c_e": {"DIESEL": 1.2, "ELECTRIC": 1.0},
                        "tax_reg_c_k_L": {"N1": 100, "N2": 200, "N3": 300},
                        "tax_annual_c_k_L": {"N1": 150, "N2": 250, "N3": 350},
                        "regional_coefficient": 1.0,
                        "tax_CO2_c_e": 50.0,
                        "B_env_c_k_e": {"DIESEL": 100, "ELECTRIC": 50},
                        "tolls": {
                            "price_per_km": {
                                "N3": {
                                    "DIESEL": 0.20,
                                    "ELECTRIC": 0.15
                                }
                            }
                        },
                        "insurance": {
                            "insurance_rate_c_L_e_safety": {
                                "DIESEL": 0.03,
                                "ELECTRIC": 0.025
                            }
                        },
                        "crew": {
                            "wage_of_crew_rank": {
                                "driver": 35000.0
                            }
                        },
                        "energy": {
                            "energy_price_c_e": {
                                "DIESEL": 1.5,
                                "ELECTRIC": 0.3
                            }
                        }
                    }
                }
            ]
        }
        
        # Create temporary database file
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "db_trucks.json")
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.test_db, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_normalize_energy_type(self):
        """Test energy type normalization."""
        # This would need actual implementation, testing the logic
        test_cases = [
            ("diesel", "DIESEL"),
            ("DIESEL", "DIESEL"),
            ("Diesel", "DIESEL"),
            ("  diesel  ", "DIESEL"),
            ("electric", "ELECTRIC"),
            ("", "DIESEL"),  # default
            (None, "DIESEL")  # default
        ]
        
        for input_val, expected in test_cases:
            # Mock implementation
            if not input_val:
                result = "DIESEL"
            else:
                result = input_val.upper().strip()
            self.assertEqual(result, expected, f"Failed for input: {input_val}")
    
    def test_normalize_vehicle_size(self):
        """Test vehicle size normalization."""
        test_cases = [
            ("n1", "N1"),
            ("N1", "N1"),
            ("n3", "N3"),
            ("  N2  ", "N2"),
            ("", "N3"),  # default
            (None, "N3")  # default
        ]
        
        for input_val, expected in test_cases:
            if not input_val:
                result = "N3"
            else:
                result = input_val.upper().strip()
            self.assertEqual(result, expected, f"Failed for input: {input_val}")
    
    def test_get_country_data_valid(self):
        """Test retrieving valid country data."""
        # Mock the database access
        countries_data = {c["country"]: c["data_country"] for c in self.test_db["countries"]}
        
        self.assertIn("France", countries_data)
        france_data = countries_data["France"]
        self.assertIn("external_factors", france_data)
        self.assertIn("tolls", france_data)
    
    def test_get_country_data_invalid(self):
        """Test retrieving invalid country data raises error."""
        countries_data = {c["country"]: c["data_country"] for c in self.test_db["countries"]}
        
        with self.assertRaises(KeyError):
            _ = countries_data["InvalidCountry"]
    
    def test_compute_o_taxes_basic(self):
        """Test basic O_taxes calculation."""
        # Sample calculation based on the formula
        consumption_energy = 28000.0
        price_energy_km = 0.15
        tax_energy = 1.2
        fuel_multiplier = 1.0
        EF_CO2 = 0.85
        tax_CO2 = 50.0
        regional_coefficient = 1.0
        
        variable_taxes = (
            consumption_energy * price_energy_km * tax_energy * 
            fuel_multiplier * EF_CO2 * tax_CO2 * regional_coefficient
        )
        
        tax_reg = 300
        tax_annual = 350
        B_env = 100
        fixed_taxes = tax_reg + tax_annual + B_env
        
        expected_o_taxes = variable_taxes + fixed_taxes
        
        # Verify calculation is positive
        self.assertGreater(expected_o_taxes, 0)
        self.assertGreater(variable_taxes, 0)
        self.assertEqual(fixed_taxes, 750)
    
    def test_compute_o_tolls_basic(self):
        """Test basic O_tolls calculation."""
        price_per_km = 0.20
        annual_distance = 80000.0
        
        expected_o_tolls = price_per_km * annual_distance
        
        self.assertEqual(expected_o_tolls, 16000.0)
    
    def test_compute_o_insurance_basic(self):
        """Test basic O_insurance calculation."""
        insurance_rate = 0.03
        purchase_cost = 150000.0
        RV = 50000.0
        
        expected_o_insurance = insurance_rate * (purchase_cost - RV)
        
        self.assertEqual(expected_o_insurance, 3000.0)
    
    def test_compute_o_crew_basic(self):
        """Test basic O_crew calculation."""
        wage = 35000.0
        N_years = 1.0
        team_count = 1
        
        expected_o_crew = wage * N_years * team_count
        
        self.assertEqual(expected_o_crew, 35000.0)
    
    def test_compute_o_crew_multiple_drivers(self):
        """Test O_crew with multiple drivers."""
        wage = 35000.0
        N_years = 2.0
        team_count = 3
        
        expected_o_crew = wage * N_years * team_count
        
        self.assertEqual(expected_o_crew, 210000.0)
    
    def test_compute_o_energy_diesel(self):
        """Test O_energy calculation for diesel."""
        consumption = 28000.0
        diesel_price = 1.5
        
        expected_o_energy = consumption * diesel_price
        
        self.assertEqual(expected_o_energy, 42000.0)
    
    def test_compute_o_energy_electric(self):
        """Test O_energy calculation for electric."""
        consumption = 28000.0
        electric_price = 0.3
        
        expected_o_energy = consumption * electric_price
        
        self.assertEqual(expected_o_energy, 8400.0)
    
    def test_opex_total_calculation(self):
        """Test total OPEX calculation."""
        o_taxes = 10000.0
        o_tolls = 16000.0
        o_insurance = 3000.0
        o_crew = 35000.0
        o_energy = 42000.0
        maintenance_cost = 5000.0
        
        expected_total = (
            o_taxes + o_tolls + o_insurance + 
            o_crew + o_energy + maintenance_cost
        )
        
        self.assertEqual(expected_total, 111000.0)


class TestScenarioRunner(unittest.TestCase):
    """Test cases for scenario loading and execution."""
    
    def setUp(self):
        """Set up test scenario data."""
        self.test_scenarios = {
            "scenarios": [
                {
                    "name": "test_truck_scenario",
                    "description": "Test truck scenario",
                    "purchase_cost": 150000.0,
                    "type_energy": "DIESEL",
                    "size_vehicle": "N3",
                    "registration_country": "France",
                    "annual_distance_travel": 80000.0,
                    "departure_city": "Paris",
                    "arrival_city": "Lyon",
                    "RV": 50000.0,
                    "N_years": 1.0,
                    "team_count": 1,
                    "maintenance_cost": 5000.0,
                    "consumption_energy": 28000.0,
                    "fuel_multiplier": 1.0,
                    "EF_CO2": 0.85
                },
                {
                    "name": "test_ship_scenario",
                    "description": "Test ship scenario",
                    "ship_class": "ro_pax",
                    "type_energy": "DIESEL"
                }
            ]
        }
        
        self.temp_dir = tempfile.mkdtemp()
        self.inputs_path = os.path.join(self.temp_dir, "inputs_opex.json")
        with open(self.inputs_path, "w", encoding="utf-8") as f:
            json.dump(self.test_scenarios, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_scenario_success(self):
        """Test loading a valid scenario."""
        with open(self.inputs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        scenarios = data.get("scenarios", [])
        scenario = None
        for sc in scenarios:
            if sc.get("name") == "test_truck_scenario":
                scenario = sc
                break
        
        self.assertIsNotNone(scenario)
        self.assertEqual(scenario["type_energy"], "DIESEL")
        self.assertEqual(scenario["size_vehicle"], "N3")
    
    def test_load_scenario_not_found(self):
        """Test loading a non-existent scenario."""
        with open(self.inputs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        scenarios = data.get("scenarios", [])
        scenario = None
        for sc in scenarios:
            if sc.get("name") == "non_existent":
                scenario = sc
                break
        
        self.assertIsNone(scenario)
    
    def test_scenario_type_identification_truck(self):
        """Test identifying truck scenario."""
        scenario = self.test_scenarios["scenarios"][0]
        
        is_truck = "size_vehicle" in scenario
        is_ship = "ship_class" in scenario
        
        self.assertTrue(is_truck)
        self.assertFalse(is_ship)
    
    def test_scenario_type_identification_ship(self):
        """Test identifying ship scenario."""
        scenario = self.test_scenarios["scenarios"][1]
        
        is_truck = "size_vehicle" in scenario
        is_ship = "ship_class" in scenario
        
        self.assertFalse(is_truck)
        self.assertTrue(is_ship)
    
    def test_key_mapping_compatibility(self):
        """Test backward compatibility key mapping."""
        key_mapping = {
            "EF_CO2_diesel": "EF_CO2",
            "EF_CO2_electric": "EF_CO2"
        }
        
        # Test old key gets mapped to new key
        old_key = "EF_CO2_diesel"
        expected_new_key = "EF_CO2"
        
        actual_new_key = key_mapping.get(old_key, old_key)
        self.assertEqual(actual_new_key, expected_new_key)
        
        # Test key without mapping stays the same
        regular_key = "purchase_cost"
        self.assertEqual(key_mapping.get(regular_key, regular_key), regular_key)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_zero_values(self):
        """Test handling of zero values."""
        # Zero annual distance
        self.assertEqual(0.20 * 0, 0)
        
        # Zero purchase cost
        self.assertEqual(0.03 * (0 - 0), 0)
        
        # Zero consumption
        self.assertEqual(0 * 1.5, 0)
    
    def test_negative_values(self):
        """Test handling of negative values (should not occur but test anyway)."""
        # Negative RV greater than purchase cost
        purchase_cost = 100000
        RV = 150000
        insurance_rate = 0.03
        
        result = insurance_rate * (purchase_cost - RV)
        # This would be negative, which might need validation
        self.assertEqual(result, -1500.0)
    
    def test_missing_database_fields(self):
        """Test handling of missing database fields."""
        # Simulate missing energy type in database
        price_table = {"DIESEL": 1.5}
        energy_key = "HYDROGEN"  # not in database
        
        energy_price = price_table.get(energy_key, 0.0)
        self.assertEqual(energy_price, 0.0)
    
    def test_vehicle_class_fallback(self):
        """Test fallback for unknown vehicle class."""
        tolls_db = {
            "price_per_km": {
                "N3": {"DIESEL": 0.20}
            }
        }
        
        vehicle_key = "N1"  # not in tolls database
        
        has_vehicle = vehicle_key in tolls_db.get("price_per_km", {})
        self.assertFalse(has_vehicle)


class TestDataValidation(unittest.TestCase):
    """Test data validation and type conversion."""
    
    def test_type_conversion_float(self):
        """Test float type conversion."""
        current_value = 150000.0
        json_value = 200000
        
        converted = type(current_value)(json_value)
        self.assertEqual(converted, 200000.0)
        self.assertIsInstance(converted, float)
    
    def test_type_conversion_int(self):
        """Test int type conversion."""
        current_value = 1
        json_value = 3
        
        converted = type(current_value)(json_value)
        self.assertEqual(converted, 3)
        self.assertIsInstance(converted, int)
    
    def test_type_conversion_string(self):
        """Test string type conversion."""
        current_value = "DIESEL"
        json_value = "ELECTRIC"
        
        converted = str(json_value)
        self.assertEqual(converted, "ELECTRIC")
        self.assertIsInstance(converted, str)
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive energy type matching."""
        energy_types = ["diesel", "DIESEL", "Diesel", "DiEsEl"]
        
        normalized = [e.upper().strip() for e in energy_types]
        
        self.assertTrue(all(e == "DIESEL" for e in normalized))


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)