from src.coin import Coin

def test_coin_creation():
    bitcoin = Coin("Bitcoin", 0.5, 50000)
    assert bitcoin.name == "Bitcoin"
    assert bitcoin.amount == 0.5
    assert bitcoin.price == 50000

def test_calculate_value():
    ethereum = Coin("Ethereum", 2.0, 3000)
    assert ethereum.calculate_value() == 6000