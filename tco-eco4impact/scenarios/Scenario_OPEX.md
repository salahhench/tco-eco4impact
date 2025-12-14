# Étude de Cas : France Long Haul 40T - 2024

Ce scénario est basé sur les données réelles et récentes du **CNR Longue Distance (Enquête 2024 sur données 2023)**.  
Il servira de **"Vérité Terrain" (Ground Truth)** pour calibrer un modèle de calcul de coûts de transport longue distance.

---

## 1. Scénario de Référence

**Nom du scénario :** France Long Haul 40T - 2024  
**Type de véhicule :** Ensemble Articulé 40T (Tracteur + Semi-remorque 3 essieux)  
**Kilométrage annuel :** 106 430 km  
**Jours d'activité :** 226 jours/an

---

## 2. Inputs (Hypothèses à entrer dans le code)

| Paramètre        | Valeur           | Notes |
|-----------------|-----------------|-------|
| Consommation    | 29,8 L/100 km   | Moyenne nationale LD |
| Prix Diesel     | 1,21 €/L (HT)   | Prix moyen pompe/cuve après récupération TICPE |
| Prix AdBlue     | 0,50 €/L        | Consommation ≈ 1,5 L/100 km (souvent négligé ou inclus) |

---

## 3. Outputs Attendus (Valeurs Cibles pour Validation)

Ces valeurs permettent de vérifier que le modèle est cohérent avec le marché français.

| Variable Code    | Valeur Cible      | Détails du calcul |
|-----------------|-----------------|-----------------|
| o_energy        | ≈ 39 000 €       | Carburant + AdBlue : (106 430 km × 29,8 L/100 km × 1,21 €) + part AdBlue |
| o_tolls         | 10 362 €         | Péages : moyenne nationale (~0,097 €/km) |
| o_insurance     | ≈ 3 500 €        | Assurances véhicule + marchandises |
| o_taxes         | ≈ 520 €          | Taxe à l'essieu (≈516 € pour un 40T standard) |
| o_crew          | ≈ 60 000 €       | Conducteur : Salaire + Charges (~48 k€) + Frais de déplacement (~12 k€) |
| o_maintenance*  | ≈ 14 400 €       | Entretien & Pneus : Entretien 10 700 € + Pneus 3 700 € |
| o_opex_total    | ≈ 172 270 €      | Somme des coûts ci-dessus + coûts de structure (~25 k€) + coût de détention du véhicule |


---

## 4. Objectif

Utiliser ces inputs pour calculer le coût de revient annuel d’un transport longue distance en France pour un 40T et comparer avec les **outputs cibles** pour valider le modèle.
