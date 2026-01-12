from src.coin import Coin
from src.portfolio import Portfolio

def test_portfolio_creation():
    portfolio = Portfolio()
    assert len(portfolio.coins) == 0

def test_add_coin():
    portfolio = Portfolio()
    bitcoin = Coin("Bitcoin", 0.5, 50000)
    portfolio.add_coin(bitcoin)
    assert len(portfolio.coins) == 1

def test_calculate_total_value():
    portfolio = Portfolio()
    bitcoin = Coin("Bitcoin", 0.5, 50000)
    ethereum = Coin("Ethereum", 2.0, 3000)
    portfolio.add_coin(bitcoin)
    portfolio.add_coin(ethereum)
    assert portfolio.calculate_total_value() == 31000