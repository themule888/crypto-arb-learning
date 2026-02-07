import asyncio
import aiohttp
import time

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

#Global Session
session = None

async def init_session():
    """Initialize the shared session with timeout configuration"""
    global session
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    print("✓ Shared session initialized with 5s timeout")
    
async def close_session():
    """Close shared session"""
    global session
    if session:
        await session.close()
        print("Shared session closed!")

# Rate limiting tracker
rate_limits = {
    'CoinGecko': [],
    'Binance': [],
    'Kraken': []
}

def track_call(exchange):
    """Track API call timestamp for rate limiting"""
    current_time = time.time()
    rate_limits[exchange].append(current_time)
    
    # Keep only last 60 seconds of calls
    rate_limits[exchange] = [t for t in rate_limits[exchange] if current_time - t < 60]
    
    # Print current rate
    calls_last_minute = len(rate_limits[exchange])
    print(f"  [{exchange}] Calls in last 60s: {calls_last_minute}")

# CoinGecko
@async_retry(max_retries=3, delay=1)
async def fetch_coingecko(coin):
    """Fetch price from CoinGecko using shared session"""
    track_call('CoinGecko')
    
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'
    
    async with session.get(url) as response:
        response.raise_for_status()
        data = await response.json()
        return {'exchange': 'CoinGecko', 'coin': coin, 'price': data[coin]['usd']}

#Binance                
@async_retry(max_retries=3, delay=1)
async def fetch_binance(coin):
    """fetching price from Binance using shared session"""
    track_call('Binance')

    symbol_map = {
        'bitcoin': 'BTCUSDT',
        'ethereum': 'ETHUSDT',
        'solana': 'SOLUSDT'
    }
    
    symbol = symbol_map[coin]
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'

    async with session.get(url) as response:
        response.raise_for_status()
        data = await response.json()
        return {'exchange': 'Binance', 'coin': coin, 'price': float(data['price'])}
    
#Kraken
@async_retry(max_retries=3, delay=1)
async def fetch_kraken(coin):
    """fetching price from Kraken using shared session"""
    track_call('Kraken')

    symbol_map = {
        'bitcoin': 'XXBTZUSD',
        'ethereum': 'XETHZUSD',
        'solana': 'SOLUSD'
    }

    pair = symbol_map[coin]
    url = f'https://api.kraken.com/0/public/Ticker?pair={pair}'

    async with session.get(url) as response:
        response.raise_for_status()
        data = await response.json()
        return {'exchange': 'Kraken', 'coin': coin, 'price': float(data['result'][pair]['c'][0])}
    
async def find_inefficiencies(coin):
    """Detect price inefficiencies between exchanges"""
    print(f'\nChecking for inefficiencies on {coin.upper()}...\n')
    
    results = await asyncio.gather(
        fetch_coingecko(coin),
        fetch_binance(coin),
        fetch_kraken(coin)
    )
    
    valid_results = [r for r in results if r is not None]
    
    if len(valid_results) < 2:
        print("Not enough valid prices to compare. Need at least 2 exchanges.")
        return
    
    print('\nAll Exchange Prices:')
    for r in valid_results:
        print(f"  {r['exchange']:12} ${r['price']:,.2f}")
    
    # Find highest and lowest
    highest = max(valid_results, key=lambda x: x['price'])
    lowest = min(valid_results, key=lambda x: x['price'])
    
    # Calculate inefficiency
    difference = highest['price'] - lowest['price']
    percent_diff = (difference / lowest['price']) * 100
    
    print(f"\nHighest: {highest['exchange']:12} ${highest['price']:,.2f}")
    print(f"Lowest:  {lowest['exchange']:12} ${lowest['price']:,.2f}")
    print(f"Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)\n")


async def main():
    """Main function to run the price checker"""
    await init_session()  # Create session first
    
    try:
        await find_inefficiencies('bitcoin')
    finally:
        await close_session()  # Always close session, even if error


if __name__ == '__main__':
    asyncio.run(main())