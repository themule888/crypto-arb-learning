class Coin:
    def __init__(self, name, amount, price):
        self.name = name
        self.amount = amount
        self.price = price
    
    def calculate_value(self):
        return self.amount * self.price

bitcoin = Coin("Bitcoin", 0.5, 50000)
ethereum = Coin("Ethereum", 2.0, 3000)
