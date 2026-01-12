class Exchange:
    def __init__(self, name):
        self.name = name
        self.prices = {}
    
    def add_price(self, coin, price):
        self.prices[coin] = price
    
    def get_price(self, coin):
        return self.prices.get(coin, 0)