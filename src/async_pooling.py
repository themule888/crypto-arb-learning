import asyncio
import aiohttp
import time
from functools import wraps

# ========================================
# DECORATOR - Copy from Session 1
# ========================================

def async_retry(max_attempts=3, delay=1):
    """Retry decorator for async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(f"  [{func.__name__}] Attempt {attempt} failed: {e}")
                        print(f"  Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"  [{func.__name__}] All {max_attempts} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator

# ========================================
# GLOBAL SESSION WITH CONNECTION POOLING
# ========================================

session = None

async def init_session():
    """Initialize shared session with optimized connection pooling"""
    global session
    
    # Connection pooling configuration
    connector = aiohttp.TCPConnector(
        limit=100,              # Max 100 total connections
        limit_per_host=10,      # Max 10 connections per exchange
        ttl_dns_cache=300,      # Cache DNS for 5 minutes
        keepalive_timeout=60    # Keep connections alive for 60s
    )
    
    # Timeout configuration
    timeout = aiohttp.ClientTimeout(total=5)
    
    # Create session with connector and timeout
    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    )
    
    print("✓ Session initialized with connection pooling:")
    print(f"  - Max connections: 100 total, 10 per host")
    print(f"  - DNS cache: 5 minutes")
    print(f"  - Keep-alive: 60 seconds")
    print(f"  - Request timeout: 5 seconds\n")

async def close_session():
    """Close shared session"""
    global session
    if session:
        await session.close()
        print("\n✓ Session closed, all connections released")

# ========================================
# RATE LIMITING TRACKER
# ========================================

rate_limits = {
    'CoinGecko': [],
    'Binance': [],
    'Kraken': []
}

def track_call(exchange):
    """Track API call for rate limiting"""
    current_time = time.time()
    rate_limits[exchange].append(current_time)
    
    # Keep only last 60 seconds
    rate_limits[exchange] = [
        t for t in rate_limits[exchange] 
        if current_time - t < 60
    ]
    
    # Print current rate
    calls_last_minute = len(rate_limits[exchange])
    print(f"  [{exchange}] Calls in last 60s: {calls_last_minute}")

# ========================================
# FETCH FUNCTIONS (Using shared session)
# ========================================

@async_retry(max_attempts=3, delay=1)
async def fetch_coingecko_price(coin='bitcoin'):
    """Fetch price from CoinGecko"""
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': coin, 'vs_currencies': 'usd'}
    
    track_call('CoinGecko')
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data[coin]['usd']
        else:
            raise Exception(f"CoinGecko API error: {response.status}")

@async_retry(max_attempts=3, delay=1)
async def fetch_binance_price(symbol='BTCUSDT'):
    """Fetch price from Binance"""
    url = f'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': symbol}
    
    track_call('Binance')
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return float(data['price'])
        else:
            raise Exception(f"Binance API error: {response.status}")

@async_retry(max_attempts=3, delay=1)
async def fetch_kraken_price(pair='XBTUSDT'):
    """Fetch price from Kraken"""
    url = 'https://api.kraken.com/0/public/Ticker'
    params = {'pair': pair}
    
    track_call('Kraken')
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            result = data['result'][pair]
            return float(result['c'][0])
        else:
            raise Exception(f"Kraken API error: {response.status}")

# ========================================
# ARBITRAGE DETECTION
# ========================================

async def find_inefficiencies(coin='bitcoin'):
    """Find price differences across exchanges"""
    
    # Fetch all prices concurrently
    results = await asyncio.gather(
        fetch_coingecko_price(coin),
        fetch_binance_price('BTCUSDT'),
        fetch_kraken_price('XBTUSDT'),
        return_exceptions=True
    )
    
    # Build price dictionary
    prices = {}
    exchanges = ['CoinGecko', 'Binance', 'Kraken']
    
    for exchange, result in zip(exchanges, results):
        if isinstance(result, Exception):
            print(f"❌ {exchange} failed: {result}")
        else:
            prices[exchange] = result
    
    if not prices:
        print("❌ No successful price fetches")
        return
    
    # Display all prices
    print("\nAll Exchange Prices:")
    for exchange, price in prices.items():
        print(f"  {exchange:12} ${price:,.2f}")
    
    # Find arbitrage opportunity
    highest_exchange = max(prices, key=prices.get)
    lowest_exchange = min(prices, key=prices.get)
    
    highest_price = prices[highest_exchange]
    lowest_price = prices[lowest_exchange]
    difference = highest_price - lowest_price
    percent_diff = (difference / lowest_price) * 100
    
    print(f"\nHighest: {highest_exchange:12} ${highest_price:,.2f}")
    print(f"Lowest:  {lowest_exchange:12} ${lowest_price:,.2f}")
    print(f"Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)")

# ========================================
# MAIN EXECUTION
# ========================================

async def main():
    """Main execution flow"""
    try:
        # Initialize session with connection pooling
        await init_session()
        
        # Find arbitrage opportunities
        await find_inefficiencies('bitcoin')
        
    finally:
        # Always close session
        await close_session()

if __name__ == '__main__':
    asyncio.run(main())