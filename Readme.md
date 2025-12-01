# Shared Python Tool for Modular Computation and Comparison of the TCO

## Overview

This project, a collaboration between the **Eco4Impact** and **EcoBoatTwin** teams, provides a shared, modular Python tool for the detailed computation and comparative analysis of the **Total Cost of Ownership (TCO)** for transport assets. It is designed to model both **trucks** and **ships**, allowing for a comprehensive financial evaluation of different powertrain technologies and operational scenarios.

The tool is built using the `cosapp` library to create a modular and extensible system. The core principle is to break down the TCO into its three fundamental components:

1.  **CAPEX (Capital Expenditure)**: The initial investment cost.
2.  **OPEX (Operational Expenditure)**: The annual running costs.
3.  **RV (Residual Value)**: The asset's value at the end of its operational life.

The final TCO is calculated as: `TCO = (Sum of Annual CAPEX) + (Sum of Annual OPEX) - RV`.

## TCO Framework Components

The calculation is broken down into the following detailed modules, as specified in the project report.

### 1. CAPEX (Capital Expenditure)
Calculated by `capex_calculator.py`, this module computes the upfront investment costs. It includes:
- **Vehicle Cost**: Purchase price for new or used assets, plus any conversion/retrofit costs.
- **Infrastructure Cost**: Hardware, software, grid connection, installation, and licensing.
- **Financials**: Taxes, subsidies, and financing costs (Capital Recovery Factor).

### 2. OPEX (Operational Expenditure)
Calculated by `Opex_Calculator_trucks.py` and `Opex_Calculator_ships.py`, this module determines the annual costs required to operate the asset. Key components include:
- **Energy**: Fuel or electricity costs based on consumption.
- **Taxes, Tolls & Ports**: Annual circulation taxes, road tolls (trucks), and port fees (ships).
- **Insurance**: Annual insurance premiums, dependent on vehicle type and value.
- **Crew**: Wages for drivers or ship crew members.
- **Maintenance**: Annual maintenance and repair costs.

### 3. RV (Residual Value)
Calculated by `rv_functions.py`, this module estimates the asset's market value at the end of the analysis period. The calculation is based on:
- **Depreciation**: Value loss from age, usage (km or hours), and maintenance investment.
- **Technical Health**: A penalty factor accounting for powertrain efficiency, technological obsolescence, remaining warranty, and battery degradation from charging behavior.
- **External Factors**: Market adjustments based on projected energy prices, CO2 taxes, and subsidies.

## System Architecture

### Main Orchestrator: `main_tco.py`
This is the main entry point for the application. It defines and runs complete TCO scenarios for different assets (e.g., a diesel truck, an electric ferry). It calls the individual CAPEX, OPEX, and RV modules with the appropriate inputs and aggregates the results to present a final TCO breakdown.

### Data-Driven Design
The tool is designed to be highly data-driven. All parameters for calculations—from tax rates to component costs—are loaded from external **JSON files** (`db_rv_trucks.json`, `db_rv_ships.json`, etc.). These files act as the project's database, with two main categories of data:
- **Country Data**: Contains country-specific parameters like taxes, wages, subsidies, and energy prices.
- **Vehicle Characteristics**: Contains asset-specific parameters for different technologies and sizes.

This design allows for easy updates and the addition of new data without changing the core Python code.

## How to Run the Project

To run a complete TCO analysis, ensure all dependencies are installed and execute the main orchestrator from your terminal:

```bash
python main_tco.py
```

This command will run the scenarios pre-defined in the script (e.g., a diesel truck in France and a cargo ship in Spain). It will print a detailed breakdown of the CAPEX, OPEX, and RV results, followed by the final TCO summary for each case.

## Getting Started

You need Git to clone the repository.

### Install Git
- **Windows**: Download from [https://git-scm.com/install/](https://git-scm.com/install/) and select your OS.
- **Linux/macOS**: Use your system's package manager (e.g., `sudo apt-get install git` or `brew install git`).

### Basic Git Configuration
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Clone the Repository
```bash
git clone https://github.com/salahhench/tco-eco4impact.git
cd tco-eco4impact
```

### View and Switch Branches
- List all local and remote branches:
    ```bash
    git branch -a
    ```
- Switch to an existing branch:
    ```bash
    git checkout <branch-name>
    ```
