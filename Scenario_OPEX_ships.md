# OPEX Calculation for Coastal Fishing Vessels - Use Case

In order to set an appropriate scenario for the **Operational Expenditure (OPEX)** for **EcoBoatTwin**, we based on the framework provided in the paper **"Total Cost of Ownership of Decarbonized Power and Propulsion Systems for Coastal Fishing Vessels"** by **Anna Sophia Hüllein** and **Ingrid Bouwer Utne**. In particular, we explain how energy consumption was extracted from the scenario presented for fishing, which describes a small fishing 10 meters vessel working 11 hours a day for both transporting and fishing tasks, and how this was extrapolated to account for different operational scenarios.

## Energy Calculation and Extrapolation

For our scenarios we take into account this small fishing vessel operating for 11 hours a day with three types of energy: **Diesel**, **BEV** and **FCET**. For this vessel, the energy consumption was computed based on fuel usage, converted into energy in kWh, with several assumptions about fuel efficiency and vessel type presented in the paper.

In our case, the energy extracted the scenario was first analyzed, which reflects the daily energy consumption of the fishing vessel operating in the specified conditions. However, to broaden the scope of the analysis, we extrapolated these figures to simulate longer work durations and larger vessels in the same category. This includes **ro-pax (roll-on/roll-off passenger ferries)** and **crew transfer vessels**, which share similar characteristics in terms of size and operational demands but different crew size and consumption (both arbitrary).

The extrapolation involved:

1. **Incrementing the hours of work** to account for vessels operating shorter/longer than 11 hours.
2. **Assuming constant travel conditions** for the new vessel categories (ro-pax and crew transfer vessels). This assumption implies that the daily operational profiles and fuel consumption rates are proportional to the base fishing vessel scenario.

## Assumptions for Fuel Energy Calculations

As part of the methodology, we used several assumptions that were explicitly outlined by the authors in their paper:

* **Fuel Efficiency Factor:** The efficiency of the fuel system was assumed to act as a factor for converting the mass of fuel into energy (in kWh) directly and adjusted according to the engine's efficiency mentionned in the cited paper. In other words, a certain percentage of the fuel’s energy is lost during conversion into mechanical power, and the efficiency factor reflects this loss in electrical terms.

## OPEX Maintenance Cost Assumption

* **Maintenance Cost:** The maintenance cost was assumed to be **15% of the total OPEX**. 

## Database Parameters

For the OPEX calculation, the parameters and assumptions used for the analysis are derived from a **db_ships.json** file that includes typical values for:

## Results

According to the parameters of the database and the inputs extrapolated from the fishing vessel case, we have the following table (which assumes an own Purchase-Residual_Value):

| Energy[kWh]/Day | Efficiency | GT  | Activity_size | Type Energy | Energy (kWh)/year | Energy Price/kWh | Crew_size | Wage/person/year | CO2 price | F1    | F2    | F3    | port_param_1 | port_param_2 | port_param_3 | port_discount_1 | port_discount_2 | Insurance | "Purchase-RV" |
|-----------------|------------|-----|---------------|-------------|-------------------|------------------|-----------|------------------|-----------|-------|-------|-------|--------------|--------------|--------------|------------------|------------------|-----------|---------------|
| 570             | 92%        | 20  | Fishing_small | Electric    | 191406            | € 150.00         | 2         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.043        | 0.468        | 0.000        | 100%             | 100%             | 2.5%      | € 66,440.00    |
| 570             | 48%        | 20  | Fishing_small | Diesel      | 99864             | € 1,500.00       | 2         | € 35,000.00      | € 70.00   | 3.206 | 0.001 | 0.048 | 0.043        | 0.468        | 0.000        | 100%             | 100%             | 2.5%      | € 172,200.00   |
| 570             | 99%        | 20  | Fishing_small | Fuel cell   | 205969.5          | € 8,000.00       | 2         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.043        | 0.468        | 0.000        | 100%             | 100%             | 2.5%      | € 49,820.00    |
| 1540            | 92%        | 105 | Ropax_small   | Electric    | 517132            | € 150.00         | 1         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.046        | 0.000        | 0.000        | 80%              | 100%             | 1.5%      | € 66,440.00    |
| 1540            | 48%        | 105 | Ropax_small   | Diesel      | 269808            | € 1,500.00       | 1         | € 35,000.00      | € 70.00   | 3.206 | 0.001 | 0.048 | 0.046        | 0.000        | 0.000        | 80%              | 100%             | 1.5%      | € 172,200.00   |
| 1540            | 99%        | 105 | Ropax_small   | Fuel cell   | 556479            | € 8,000.00       | 1         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.046        | 0.000        | 0.000        | 80%              | 100%             | 1.5%      | € 49,820.00    |
| 440             | 92%        | 20  | CTV_small     | Electric    | 147752            | € 150.00         | 5         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.000        | 0.000        | 0.000        | 80%              | 100%             | 2.0%      | € 66,440.00    |
| 440             | 48%        | 20  | CTV_small     | Diesel      | 77088             | € 1,500.00       | 5         | € 35,000.00      | € 70.00   | 3.206 | 0.001 | 0.048 | 0.000        | 0.000        | 0.000        | 80%              | 100%             | 2.0%      | € 172,200.00   |
| 440             | 99%        | 20  | CTV_small     | Fuel cell   | 158994            | € 8,000.00       | 5         | € 35,000.00      | € -       | 0.000 | 0.000 | 0.000 | 0.000        | 0.000        | 0.000        | 80%              | 100%             | 2.0%      | € 49,820.00    |

The following table shows the expected outputs from the OPEX module from the previous inputs:

| O_taxes        | O_ports   | O_insurance   | O_crew     | O_energy        | O_maintenance    | OPEX              |
|----------------|-----------|---------------|------------|-----------------|------------------|-------------------|
| € -            | € 3,730.30| € 19,932.00   | € 70,000.00| € 28,710,900.00 | € 5,083,158.05   | € 33,887,720.35   |
| € 325,067.31   | € 3,730.30| € 51,660.00   | € 70,000.00| € 149,796,000.00| € 26,514,080.75  | € 176,760,538.36  |
| € -            | € 3,730.30| € 14,946.00   | € 70,000.00| € 1,647,756,000.00 | € 290,796,119.35 | € 1,938,640,795.65|
| € -            | € 1,422.62| € 11,959.20   | € 35,000.00| € 77,569,800.00 | € 13,697,326.20  | € 91,315,508.03   |
| € 878,252.02   | € 1,422.62| € 30,996.00   | € 35,000.00| € 404,712,000.00| € 71,586,647.76  | € 477,244,318.41  |
| € -            | € 1,422.62| € 8,967.60    | € 35,000.00| € 4,451,832,000.00 | € 785,625,421.80 | € 5,237,502,812.03|
| € -            | € -       | € 15,945.60   | € 175,000.00| € 22,162,800.00 | € 3,944,778.64   | € 26,298,524.24   |
| € 250,929.15   | € -       | € 41,328.00   | € 175,000.00| € 115,632,000.00| € 20,488,104.20  | € 136,587,361.35  |
| € -            | € -       | € 11,956.80   | € 175,000.00| € 1,271,952,000.00| € 224,495,110.02 | € 1,496,634,066.82|
