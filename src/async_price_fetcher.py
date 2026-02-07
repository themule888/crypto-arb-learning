import aiohttp
import asyncio
import time

# This is our ASYNC version of fetching prices
# Notice 'async def' instead of just 'def'
async def fetch_coingecko_price(coin):
    """Fetch price from CoinGecko - ASYNC version"""
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': coin, 'vs_currencies': 'usd'} 
    
    try:
        # aiohttp requires a 'session' - think of it like opening a connection
        async with aiohttp.ClientSession() as session:
            # Now we make the actual GET request
            # Notice the 'await' - this is where we pause and let other tasks run
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    # We need 'await' here too because .json() is async
                    data = await response.json()
                    if coin in data:
                        return {'exchange': 'CoinGecko', 'coin': coin, 'price': data[coin]['usd']}
                    else:
                        return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': 'Coin not found'}
                else:
                    return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    
    except Exception as e:
        return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': str(e)}


async def fetch_coincap_price(coin):
    """Fetch price from CoinCap - ASYNC version"""
    # CoinCap uses different URL structure: /v2/assets/{coin}
    url = f'https://api.coincap.io/v2/assets/{coin}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'priceUsd' in data['data']:
                        price = float(data['data']['priceUsd'])
                        return {'exchange': 'CoinCap', 'coin': coin, 'price': price}
                    else:
                        return {'exchange': 'CoinCap', 'coin': coin, 'price': None, 'error': 'Data not found'}
                else:
                    return {'exchange': 'CoinCap', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    
    except Exception as e:
        return {'exchange': 'CoinCap', 'coin': coin, 'price': None, 'error': str(e)}


async def fetch_binance_price(coin):
    """Fetch price from Binance - ASYNC version"""
    # Binance uses trading pairs like BTCUSDT (not just 'bitcoin')
    # We need to convert: bitcoin -> BTC, ethereum -> ETH
    symbol_map = {
        'bitcoin': 'BTCUSDT',
        'ethereum': 'ETHUSDT',
        'solana': 'SOLUSDT'
    }
    
    if coin not in symbol_map:
        return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': 'Coin not supported'}
    
    symbol = symbol_map[coin]
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'price' in data:
                        price = float(data['price'])
                        return {'exchange': 'Binance', 'coin': coin, 'price': price}
                    else:
                        return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': 'Price not found'}
                else:
                    return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    
    except Exception as e:
        return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': str(e)}


async def fetch_all_prices_async(coin):
    """
    Fetch from ALL exchanges SIMULTANEOUSLY using asyncio.gather()
    This is the magic - all 3 API calls happen at the same time
    """
    print(f'\n🚀 Fetching {coin} prices ASYNC (all at once)...')
    
    # Record start time
    start_time = time.time()
    
    # asyncio.gather() runs all these functions simultaneously
    # It waits for ALL of them to complete, then returns results as a list
    results = await asyncio.gather(
        fetch_coingecko_price(coin),
        fetch_coincap_price(coin),
        fetch_binance_price(coin)
    )
    
    # Calculate how long it took
    elapsed = time.time() - start_time
    
    # Display results
    print(f'\n⏱️  ASYNC completed in {elapsed:.3f} seconds\n')
    
    for result in results:
        if result['price']:
            print(f"{result['exchange']:12} ${result['price']:,.2f}")
        else:
            print(f"{result['exchange']:12} ERROR: {result['error']}")
    
    return results


async def find_inefficiencies(coin):
    """
    Detect price inefficiencies between exchanges
    """
    print(f'\n💰 Checking for inefficiencies on {coin.upper()}...\n')
    
    # Fetch from all exchanges
    results = await asyncio.gather(
        fetch_coingecko_price(coin),
        fetch_coincap_price(coin),
        fetch_binance_price(coin)
    )
    
    # Filter out errors
    valid_results = [r for r in results if r['price'] is not None]
    
    if len(valid_results) < 2:
        print('❌ Not enough data to compare')
        return
    
    # Find highest and lowest prices
    highest = max(valid_results, key=lambda x: x['price'])
    lowest = min(valid_results, key=lambda x: x['price'])
    
    # Calculate inefficiency
    difference = highest['price'] - lowest['price']
    percent_diff = (difference / lowest['price']) * 100
    
    print(f"Highest: {highest['exchange']:12} ${highest['price']:,.2f}")
    print(f"Lowest:  {lowest['exchange']:12} ${lowest['price']:,.2f}")
    print(f"\n📊 Price difference: ${difference:,.2f} ({percent_diff:.3f}%)")
    
    if percent_diff > 0.1:  # If more than 0.1% difference
        print(f"✅ INEFFICIENCY DETECTED!")
        print(f"   Strategy: Buy on {lowest['exchange']}, sell on {highest['exchange']}")
        print(f"   Potential profit per coin: ${difference:,.2f}")
    else:
        print(f"⚪ No significant inefficiency (< 0.1%)")


# Main execution
if __name__ == '__main__':
    print('\n🎯 WEEK 14 - SESSION 1: Async Programming\n')
    
    # Find inefficiencies
    asyncio.run(find_inefficiencies('bitcoin'))
    
    print('\n✅ Complete! You just ran async code.')