import asyncio
import aiohttp
import websockets
import json
import time
import csv
from datetime import datetime

# Retry Deocrator
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
                        print(f' Attemp {attempt + 1} failed: {e}. Retrying in {wait_time}s...')
                        await asyncio.sleep(wait_time)
                    else:
                        print(f'All {max_retries} attempts failed for {func.__name__}')
                        return None
        return wrapper
    return decorator

# Global Session
session = None

async def init_session():
    """Initilize the shared session with timeout configuration and connection pooling"""
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
    print('✓ Share session initialized with 5s timeout and connection pooling')

async def close_session():
    """Closed shared session"""
    global session
    if session:
        await session.close()
        print('Share session closed!')

# Rate Limiting tracker
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
    print(f'  [{exchange}] Calls in last 60s: {calls_last_minute}')

# WebSocket price storage
latest_ws_prices = {
    'BTC': None,
    'ETH': None
}

# WebSocket reconnection settings
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 2

# CSV Logging funtion
def log_to_csv(coin, prices, spread):
    """Log price data to CSV file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Open CSV File in append mode
    with open('price_monitoring.csv', 'a', newline='') as file:
        writer = csv.writer(file)

        # Writer header if file is new/empty
        try:
            if file.tell() == 0: # File is empty
                writer.writerow(['Timestamp', 'Coin', 'CoinGecko', 'Biance', 'Kraken', 'Spread_USD', 'Spread_Percent'])
        except:
            pass

        # Writer price data
        writer.writerow([
            timestamp,
            coin,
            prices.get('CoinGecko', 'N/A'),
            prices.get('Binance', 'N/A'),
            prices.get('Kraken', 'N/A'),
            f'{spread["difference"]:.2f}',
            f'{spread["percent"]:.3f}'
        ])

# CoinGecko
@async_retry (max_retries= 3, delay=1)

async def fetch_coingecko(coin):
    """Fetch price from Coingecko using shared session"""
    track_call('CoinGecko')

    url = url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'

    async with session.get(url) as response:
        response.raise_for_status()
        data = await response.json()

    return{'exchnage': 'CoinGecko', 'coin': coin, 'price': data[coin]['usd']}

# Binance HTTP
@async_retry(max_retries=3, delay=1)
async def fetch_binance(coin):
    """Fetching price from Binance using shared session"""
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
    
# Kraken
@async_retry (max_retries=3, delay=1)
async def fetch_kraken(coin):
    """Fetching price from Kraken using shared session"""
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

# WebSocket streaming
async def stream_binance_websocket(symbol, display_name):
    """Stream real-time prices from Binance WebSocket with auto-reconnect"""
    url = f'wss://stream.binance.com:9443/ws/{symbol.lower()}@trade'

    reconnect_count = 0

    while reconnect_count < MAX_RECONNECT_ATTEMPTS:
        try:
            print(f'🔌 Connecting to {display_name} WebSocket stream...')

            async with websockets.connect(url) as ws:
                print(f'✅ {display_name} WebSocket connected!')
                reconnect_count = 0 # Reset on successful connection

                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    price = float(data['p'])

                    # Update latest WebSocket price
                    latest_ws_prices[display_name] = price
        except websockets.exceptions.ConnectionClosed:
            reconnect_count += 1
            print(f'❌ {display_name} WebSocket disconnected. Reconnecting... ({reconnect_count}/{MAX_RECONNECT_ATTEMPTS})')
            await asyncio.sleep(MAX_RECONNECT_ATTEMPTS)
        
        except Exception as e:
            reconnect_count += 1
            print(f'❌ {display_name} WebSocket error: {e}. Reconnecting...({reconnect_count}/{MAX_RECONNECT_ATTEMPTS})')
            await asyncio.sleep(MAX_RECONNECT_ATTEMPTS)
    
    print(f'⛔ {display_name} WebSocket - Max reconnection attempts reached')

async def display_websocket_prices():
    """Display WebSocket prices every 1 second"""
    print('\n📊 WebSocket Price Display Started (updates every 1 second)')
    print('=' * 60)

    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')

            btc = latest_ws_prices['BTC']
            eth = latest_ws_prices['ETH']

            btc_display = f'${btc:,.2f}' if btc else 'Waiting...'
            eth_display = f'${eth:,.2f}' if eth else 'Waiting...'

            print(f'[{timestamp}] BTC: {btc_display:>12} | ETH: {eth_display:12}')

            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        print('\n\n⛔️ WebSocket display stopped')

async def find_inefficiencies(coin):
    """Find price inefficiencies across exchanges"""


    # Fetch all prices concurrently
    results = await asyncio.gather(
        fetch_coingecko(coin),
        fetch_binance(coin),
        fetch_kraken(coin),
        return_exceptions=True
    )

    # Build price dicitionary
    prices = {}
    exchanges = ['CoinGecko', 'Binance', 'Kraken']

    for exchange, result in zip(exchanges, results):
        if isinstance(result, Exception):
            print(f'❌ {exchange} failed: {result}')
        elif result is None:
            print(f'❌ {exchange} failed: All retries exhausted')
        else:
            prices[exchange] = result['price']
    
    if not prices:
        print(f'❌ No successful prices fetches')
        return None
    
    # Display all pries
    print(f'\nHTTP API Prices:')
    for exchange, price in prices.items():
        print(f'  {exchange:12} ${price:,.2f}')

    # Find Arb Opp
    highest_exchange = max(prices, key=prices.get)
    lowest_exchange = min(prices, key=prices.get)

    highest_price = prices[highest_exchange]
    lowest_price = prices[lowest_exchange]
    difference = highest_price - lowest_price
    percent_diff = (difference / lowest_price) * 100

    print(f'\nHighest: {highest_exchange:12} ${highest_price:,.2f}')
    print(f'Lowest:  {lowest_exchange:12} ${lowest_price:,.2f}')
    print(f'Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)')

    # Return data for logging
    spread = {
        'difference': difference,
        'percent': percent_diff
    }

    return prices, spread

# Monitoring Loop
async def monitor_continously(coin='bitcoin', interval=30):
    """Monitor prices continously via GTTP and log to CSV"""
    print(f'\n🔍 Starting HTTP monitoring for {coin.upper()}')
    print(f'📊 Checking every {interval} seconds')
    print(f'📁 Logging to: price_monitoring.csv')
    print(f'Press Ctrl+C stop\n')
    print('=' * 60)

    check_count = 0

    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f'\n[HTTP check #{check_count}] {timestamp}')
            print('-' * 60)

            # Find Price differences
            result = await find_inefficiencies(coin)

            # Log to CSV if successful
            if result:
                prices, spread = result
                log_to_csv(coin, prices, spread)
                print(f'✓ Logged to CSV')

            # Wait before next check
            print(f'⏳ Next HTTP check in {interval} seconds ...')
            print('=' * 60)
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print(f'\n\n⛔️ HTTP monitoring stopped by user')
        print(f'📊 Totsl hecks performed: {check_count}')

async def compare_http_websocket():
    """Compare HTTP vs WebSocket prices every 30 seconds"""
    await asyncio.sleep(5) # Wait for WebSocket to connect first

    while True:
        try:
            # Fetch HTTP Prices
            params = {'ids': 'bitcoin,ethereum', 'vs_currencies': 'usd'}

            async with session.get('https://api.coingecko.com/api/v3/simple/price', params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    btc_http = data['bitcoin']['usd']
                    eth_http = data['ethereum']['usd']

                    btc_ws = latest_ws_prices['BTC']
                    eth_ws = latest_ws_prices['ETH']

                    if btc_ws and eth_ws:
                        btc_diff = abs(btc_ws - btc_http)
                        eth_diff = abs(eth_ws - eth_http)

                        print(f'\n🔍 HTTP vs WebSocket Comparison:')
                        print(f'  BTC - HTTP: ${btc_http:,.2f} | WebSocket: ${btc_ws:,.2f} | Diff: ${btc_diff}')
                        print(f'  ETH - HTTP: ${eth_http:,.2f} | WebSocket: ${eth_ws:,.2f} | Diff: ${eth_diff}')
        
        except Exception as e:
            print(f'❌ HTTP comparison error {e}')

        await asyncio.sleep(30)


async def main():
    """Main execution flow - runs HTTP monitoring AND WebSocket streaming"""
    try:
        # Init session with connection poooling
        await init_session()

        # Run All Task simultaneuously
        await asyncio.gather(
            # HTTP monitoring (original functionality)
            monitor_continously(coin='bitcoin', interval=30),

            # WebSocket streaming (new functionality)
            stream_binance_websocket('btcusdt', 'BTC'),
            stream_binance_websocket('ethusdt', 'ETH'),
            display_websocket_prices(),

            # HTTP vs WebSocket comparison
            compare_http_websocket()
        )
    
    finally:
        # Alaways close session
        await close_session()

if __name__ == '__main__':
    asyncio.run(main())
    