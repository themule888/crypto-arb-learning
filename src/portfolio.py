from src.coin import Coin

class Portfolio:
    def __init__(self):
        self.coins = []

    def add_coin(self, coin):
        self.coins.append(coin)

    def calculate_total_value(self):
        total = 0
        for coin in self.coins:
            total = total + coin.calculate_value()
        return total
        

