from cosapp.base import Port

class CountryPropertiesPort(Port):
    '''
    Port for Country Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        self.add_variable('energy_price', dtype=float, desc='Energy price ($/L)', value=0.0)
        self.add_variable('c02_taxes', dtype=float, desc='CO2 taxes ($)', value=0.0)
        self.add_variable('subsidies', dtype=float, desc='Subsidies ($)', value=0.0)


        # SHIP OPEX
        self.add_variable(
            "crew_monthly_total",
            dtype=float,
            desc="Total monthly crew cost (EUR). If 0, use seafarer * crew size.",
            value=0.0
        )

        # Opex Trucks
        self.add_variable("departure_city", dtype=str, desc="Departure city", value="Paris")
        self.add_variable("arrival_city", dtype=str, desc="Arrival city", value="Marseille")

