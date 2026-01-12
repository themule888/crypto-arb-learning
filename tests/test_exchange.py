from src.exchange import Exchange

def test_exchange_creation():
    uniswap = Exchange("Uniswap")
    assert uniswap.name == "Uniswap"
    assert len(uniswap.prices) == 0

def test_add_price():
    uniswap = Exchange("Uniswap")
    uniswap.add_price("Bitcoin", 50000)
    assert uniswap.get_price("Bitcoin") == 50000

def test_get_price_missing_coin():
    uniswap = Exchange("Uniswap")
    assert uniswap.get_price("Dogecoin") == 0