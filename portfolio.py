from coin import Coin

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
        
my_portfolio = Portfolio()

bitcoin = Coin('Bitcoin', 0.5, 50000)
ethereum = Coin('Ethereum', 2.0, 3000)
solana = Coin('Solana', 10.0, 100)

my_portfolio.add_coin(bitcoin)
my_portfolio.add_coin(ethereum)
my_portfolio.add_coin(solana)

print(f'Portfolio has {len(my_portfolio.coins)} coins')
print(f'Total portfolio value: ${my_portfolio.calculate_total_value()}')


