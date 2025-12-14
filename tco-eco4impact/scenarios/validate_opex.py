import sys
import os
import json
from cosapp.drivers import RunOnce

# =============================================================================
# 1. CONFIGURATION DES CHEMINS (IMPORTS)
# =============================================================================
# On récupère le dossier où se trouve ce script (scenarios)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# On remonte d'un niveau pour trouver la racine du projet (tco-eco4impact)
project_root = os.path.dirname(current_script_dir)

# On définit le dossier des fonctions
functions_dir = os.path.join(project_root, "functions")

# On ajoute ce dossier à Python pour qu'il puisse faire l'import
sys.path.append(functions_dir)

# Maintenant, on peut importer ta classe
try:
    from Opex_Calculator import TruckOPEXCalculator
    print(f"✅ Module importé depuis : {functions_dir}")
except ImportError as e:
    print(f"❌ ERREUR CRITIQUE : Impossible d'importer Opex_Calculator.")
    print(f"   Chemin cherché : {functions_dir}")
    print(f"   Détail : {e}")
    sys.exit(1)

# =============================================================================
# 2. CLASSE DE VALIDATION
# =============================================================================

class OPEXValidator:
    """
    Classe de validation pour comparer les résultats avec le CNR France 40T (2024).
    """

    def __init__(self, system_instance):
        self.system = system_instance

    def load_cnr_scenario_inputs(self):
        """Injecte les hypothèses du CNR 2024."""
        print("... Chargement du scénario CNR France 40T (2024) ...")

        # Hypothèses Physiques
        self.system.registration_country = "France"
        self.system.size_vehicle = "N3"
        self.system.type_energy = "DIESEL"
        self.system.annual_distance_travel = 106430.0
        self.system.team_count = 1
        self.system.N_years = 1.0
        
        # Coûts directs
        self.system.maintenance_cost = 14400.0 
        
        # Consommation forcée (pour matcher 29.8L/100km)
        conso_l_100 = 29.8
        total_liters = (106430.0 / 100.0) * conso_l_100
        self.system.consumption_energy = total_liters 
        
        # Amortissement estimé
        self.system.purchase_cost = 120000.0 
        self.system.RV = 20000.0 
        self.system.EF_CO2 = 3.16 
        self.system.fuel_multiplier = 1.0

    def run_comparison(self):
        """Exécute et compare."""
        # Ajout du driver si nécessaire
        if not hasattr(self.system, 'drivers') or 'validation_run' not in self.system.drivers:
            self.system.add_driver(RunOnce("validation_run"))
        
        self.system.run_drivers()

        # Cibles CNR 2024
        targets = {
            "o_energy": 39000.0,
            "o_tolls": 10362.0,
            "o_insurance": 3500.0,
            "o_taxes": 520.0,
            "o_crew": 60000.0,
            "o_opex_total": 172270.0
        }

        print("\n" + "="*85)
        print(f"{' RAPPORT DE VALIDATION - CNR FRANCE 40T ' :^85}")
        print("="*85)
        print(f"{'POSTE':<20} | {'CALCULÉ (€)':<15} | {'CIBLE CNR (€)':<15} | {'DELTA (%)':<10} | {'STATUS'}")
        print("-" * 85)

        results = {
            "o_energy": self.system.o_energy,
            "o_tolls": self.system.o_tolls,
            "o_insurance": self.system.o_insurance,
            "o_taxes": self.system.o_taxes,
            "o_crew": self.system.o_crew,
            "o_opex_total": self.system.o_opex_total
        }

        for key, target in targets.items():
            calculated = results.get(key, 0.0)
            diff = calculated - target
            delta_pct = (diff / target) * 100 if target != 0 else 0.0

            if abs(delta_pct) < 10: status = "✅ OK"
            elif abs(delta_pct) < 25: status = "⚠️ WARN"
            else: status = "❌ FAIL"

            print(f"{key:<20} | {calculated:12,.0f} € | {target:12,.0f} € | {delta_pct:+9.1f}% | {status}")

        print("-" * 85 + "\n")

# =============================================================================
# 3. EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    # Définition du chemin vers la base de données
    # On suppose qu'elle est dans tco-eco4impact/database/db_trucks.json
    db_path = os.path.join(project_root, "database", "db_trucks_doc.json")

    # Vérification
    if not os.path.exists(db_path):
        print(f"⚠️  ATTENTION : Base de données introuvable !")
        print(f"   Chemin cherché : {db_path}")
    else:
        print(f"✅ Base de données trouvée : {db_path}")
    
    # Lancement
    my_truck = TruckOPEXCalculator("ValidationUnit", db_path=db_path)
    validator = OPEXValidator(my_truck)
    validator.load_cnr_scenario_inputs()
    validator.run_comparison()
