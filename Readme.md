# RESIDUAL VALUE

## Summary

This project is designed to calculate the residual value of vehicles, considering various factors. It is built using the `cosapp` library, which provides a framework for creating and connecting systems.

### `rv_functions.py`

This file contains the core logic for the residual value calculation. It is structured as a `cosapp` system, which allows for modular and extensible design.

**Key Components:**

- **`VehiclePropertiesPort` and `CountryPropertiesPort`**: These are `cosapp` Ports that define the input data required for the calculation. They include vehicle-specific data (e.g., type, cost, age) and country-specific data (e.g., energy prices, taxes).
- **`ResidualValueCalculator`**: This is the main `cosapp` System. It takes the data from the input ports and calculates the residual value through a series of steps:
    1.  **Depreciation**: Calculates the loss of value due to age, usage, and maintenance.
    2.  **Impact Health**: A penalty that accounts for the vehicle's condition, including:
        - **Efficiency**: How efficient the vehicle is compared to a benchmark.
        - **Obsolescence**: A penalty for outdated technology.
        - **Charging**: For electric vehicles, this considers the degradation due to charging habits.
        - **Warranty**: The effect of the remaining warranty on the vehicle's value.
    3.  **External Factors**: Adjustments based on economic factors like fuel prices, CO2 taxes, and government subsidies.

The `ResidualValueCalculator` loads its parameters from a JSON file (e.g., `db_rv_trucks.json`), which makes it easy to update the data without changing the code.

### `main_test.py`

This file serves as an example of how to use the `ResidualValueCalculator`. It is also the place where other developers can integrate their own calculations, such as OPEX (Operational Expenditure) and CAPEX (Capital Expenditure).

## Donwload the project
To donwload this repository you should have Git:
### Install Git
- Windows: download from https://git-scm.com/install/ and select you OS

### Basic configuration
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Clone the repository
- HTTPS:
    ```
    git clone https://github.com/salahhench/tco-eco4impact.git
    cd $NAME_THE_REPO
    ```

### See and switch branches
```
git branch -a           # list local and remote branches
```
- Switch to an existing branch:
    ```
    git checkout RV
    ```
