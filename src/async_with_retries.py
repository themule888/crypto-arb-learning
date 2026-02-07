import asyncio
import aiohttp

#Decorator
def async_retry(max_retries=3, delay=1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"All {max_retries} attempts failed for {func.__name__}")
                        return None
        return wrapper
    return decorator

#CoinGecko
@async_retry(max_retries=3, delay=1)
async def fetch_coingecko(coin):
    """fetching price from CoinGecko"""
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return {'exchange': 'CoinGecko', 'coin': coin, 'price': data[coin]['usd']}

#Binance                
@async_retry(max_retries=3, delay=1)
async def fetch_binance(coin):
    """fetching price from Binance"""
    symbol_map = {
        'bitcoin': 'BTCUSDT',
        'ethereum': 'ETHUSDT',
        'solana': 'SOLUSDT'
    }
    
    symbol = symbol_map[coin]
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return {'exchange': 'Binance', 'coin': coin, 'price': float(data['price'])}
        
#Kraken
@async_retry(max_retries=3, delay=1)
async def fetch_kraken(coin):
    """fetching price from Kraken"""
    symbol_map = {
        'bitcoin': 'XXBTZUSD',
        'ethereum': 'XETHZUSD',
        'solana': 'SOLUSD'
    }

    pair = symbol_map[coin]
    url = f'https://api.kraken.com/0/public/Ticker?pair={pair}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return {'exchange': 'Kraken', 'coin': coin, 'price': float(data['result'][pair]['c'][0])}

async def find_inefficiencies(coin):
    """Detect price inefficiencies between exchanges"""
    print(f'\n Checking for inefficiencies on {coin.upper()}...\n')

    results = await asyncio.gather(
        fetch_coingecko(coin),
        fetch_binance(coin),
        fetch_kraken(coin)
    )

    valid_results = [r for r in results if r is not None]

    if len(valid_results) < 2:
        print("Not enough valid prices to compare. Need at least 2 exchanges.")
        return

    print('All Exchange Prices:')
    for r in valid_results:
        print(f"{r['exchange']:12} ${r['price']:,.2f}")
 

    # Find Highest and Lowest
    highest = max(valid_results, key=lambda x: x['price'])
    lowest = min(valid_results, key=lambda x: x['price'])

    #Calculate Inefficiency
    difference = highest['price'] - lowest['price']
    percent_diff = (difference / lowest['price']) * 100

    print(f'Highest: {highest['exchange']:12} ${highest['price']:,.2f}')
    print(f'Lowest: {lowest['exchange']:12} ${lowest['price']:,.2f}')
    print(f'\n Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)')

if __name__ == '__main__':
    asyncio.run(find_inefficiencies('bitcoin'))
    
  