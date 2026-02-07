import asyncio
import aiohttp
import time
import csv
from datetime import datetime

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
    """Initialize the shared session with timeout configuration and connection pooling"""
    global session
    
    # Connection pooling configuration
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=10,
        ttl_dns_cache=300,
        keepalive_timeout=60
    )
    
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    print("✓ Shared session initialized with 5s timeout and connection pooling")
    
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

# CSV Logging Function

def log_to_csv(coin, prices, spread):
    """Log price data to CSV file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #Open CSV File in append mode
    with open('price_monitoring.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        
        #Write header if file is new/empty
        try:
            if file.tell() == 0: # File is empty
                writer.writerow(['Timestamp', 'Coin', 'CoinGecko', 'Binance', 'Kraken', 'Spread_USD', 'Spread_Percent'])
        except:
            pass

        #Write price data
        writer.writerow([
            timestamp,
            coin,
            prices.get('CoinGecko', 'N/A'),
            prices.get('Binance', 'N/A'),
            prices.get('Kraken', 'N/A'),
            f'{spread['difference']:.2f}',
            f'{spread['percent']:.3f}'
        ])

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
    """Find price inefficiencies across exchanges"""
    
    # Fetch all prices concurrently
    results = await asyncio.gather(
        fetch_coingecko(coin),
        fetch_binance(coin),
        fetch_kraken(coin),
        return_exceptions=True
    )
    
    # Build price dictionary
    prices = {}
    exchanges = ['CoinGecko', 'Binance', 'Kraken']

    for exchange, result in zip(exchanges, results):
        if isinstance(result, Exception):
            print(f'❌ {exchange} failed: {result}')
        else:
            prices[exchange] = result['price'] 
    
    if not prices:
        print(f'❌ No successful prices fetches')
        return None
    
    # Display all prices
    print("\nAll Exchange Prices:")
    for exchange, price in prices.items():
        print(f' {exchange:12} ${price:,.2f}')

    #Find arb opportunity
    highest_exchange = max(prices, key=prices.get)
    lowest_exchange = min(prices, key=prices.get)

    highest_price = prices[highest_exchange]
    lowest_price = prices[lowest_exchange]
    difference = highest_price - lowest_price
    percent_diff = (difference / lowest_price) * 100

    print(f'\nHighest: {highest_exchange:12} ${highest_price:,.2f}')
    print(f'Lowest:  {lowest_exchange:12} ${lowest_price:,.2f}')
    print(f'Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)')

    #Return data for logging
    spread = {
        'difference': difference,
        'percent': percent_diff
    }

    return prices, spread

# Monitoring Loop Function
async def monitor_continuously(coin='bitcoin', interval=30):
    """Monitor prices continuously and log to CSV"""
    print(f'\n🔁 Starting continuous monitoring for {coin.upper()}')
    print(f'📊 Checking every {interval} seconds')
    print(f'📂 Logging to: price_monitoring.csv')
    print(f' Press Crtl+C to stop\n')
    print('=' * 60)

    check_count = 0

    try:
        while True: #Infinite Loop
            check_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            print(f'\n[Check #{check_count}] {timestamp}')
            print('-' * 60)

            # Find Price differences

            result = await find_inefficiencies(coin)

            # Log to CSV if successful
            if result:
                prices, spread = result
                log_to_csv(coin, prices, spread)
                print(f'✓ Logged to CSV')

            # Wait before next check
            print(f'\n⏳ Next check in {interval} seconds ...')
            print('=' * 60)
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print(f'\n\n Monitoring stooped by user')
        print(f'📊 Total Checks performed: {check_count}')


async def main():
    """Main excecution flow"""
    try:
        #Init session with connection pooling
        await init_session()

        # Start continuous monitoring
        await monitor_continuously(coin= 'bitcoin', interval=30)

    finally:
        #Always close session
        await close_session()


if __name__ == '__main__':
    asyncio.run(main())