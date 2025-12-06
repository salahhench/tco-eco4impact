from cosapp.base import Port

class CountryPropertiesPort(Port):
    '''
    Port for Country Properties inputs and outputs for ships and trucks.
    '''

    def setup(self):
        self.add_variable('energy_price', dtype=float, desc='Energy price ($/L)', value=0.0)
        self.add_variable('c02_taxes', dtype=float, desc='CO2 taxes ($)', value=0.0)
        self.add_variable('subsidies', dtype=float, desc='Subsidies ($)', value=0.0)
