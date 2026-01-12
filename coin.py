class Coin:
    def __init__(self, name, amount, price):
        self.name = name
        self.amount = amount
        self.price = price
    
    def calculate_value(self):
        return self.amount * self.price
    

