import aiohttp
import asyncio
import time

async def fetch_coingecko_price(coin):
    """fetching price from CoinGecko"""
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': coin, 'vs_currencies': 'usd'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin in data:
                        return {'exchange': 'CoinGecko', 'coin': coin, 'price': data[coin]['usd']}
                    else:
                        return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': 'Coin not found'}
                else:
                    return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    except Exception as e:
        return {'exchange': 'CoinGecko', 'coin': coin, 'price': None, 'error': str(e)}
    

async def fetch_binance_price(coin):
    """fetching price from Binance"""
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
                        return {'exchange': 'Binance', 'coin': coin, 'price': float(data['price'])}
                    else:
                        return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': 'Price not found'}
                else:
                    return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    except Exception as e:
        return {'exchange': 'Binance', 'coin': coin, 'price': None, 'error': str(e)}
    

    
async def fetch_kraken_price(coin):
    """fetching price from Kraken"""
    symbol_map = {
        'bitcoin': 'XXBTZUSD',
        'ethereum': 'XETHZUSD',
        'solana': 'SOLUSD'
    }

    if coin not in symbol_map:
        return {'exchange': 'Kraken', 'coin': coin, 'price': None, 'error': 'Coin not supported'}
    
    symbol = symbol_map[coin]
    url = f'https://api.kraken.com/0/public/Ticker?pair={symbol}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data and symbol in data['result']:
                        return {'exchange': 'Kraken', 'coin': coin, 'price': float(data['result'][symbol]['c'][0])}
                    else:
                        return {'exchange': 'Kraken', 'coin': coin, 'price': None, 'error': 'Price not found'}
                else:
                    return {'exchange': 'Kraken', 'coin': coin, 'price': None, 'error': f'Status {response.status}'}
    except Exception as e:
        return {'exchange': 'Kraken', 'coin': coin, 'price': None, 'error': str(e)}
    



async def find_inefficiencies(coin):
    """Detect price inefficiencies between exchanges"""
    print(f'\n Checking for inefficiencies on {coin.upper()}...\n')
    results = await asyncio.gather(
        fetch_coingecko_price(coin),
        fetch_binance_price(coin),
        fetch_kraken_price(coin)
    )

    valid_results = [r for r in results if r['price'] is not None]
        
    print("All Exchange Prices:")
    for r in valid_results:
        if r['price']:
            print(f"  {r['exchange']:12} ${r['price']:,.2f}")
    print()

    if len(valid_results) < 2:
        print('Not enough data to compare')
        return
    
    # Find Highest and Lowest Prices
    highest = max(valid_results, key=lambda x: x['price'])
    lowest = min(valid_results, key=lambda x: x['price'])

    # Calculate the Inefficiency
    difference = highest['price'] - lowest['price']
    percent_diff = (difference / lowest['price']) * 100

    print(f'Highest: {highest['exchange']:12} ${highest['price']:,.2f}')
    print(f'Lowest: {lowest['exchange']:12} ${lowest['price']:,.2f}')
    print(f'\n Price Difference: ${difference:,.2f} ({percent_diff:.3f}%)')

    if percent_diff > 0.1:
        print('INEFFICIENCY DETECTED')
        print(f'Strategy: Buy on {lowest['exchange']}, sell on {highest['exchange']}')
        print(f'Potential profit per coin: ${difference:,.2f}')
    else:
        print('No significant inefficiecy (< 0.1%)')

if __name__ == '__main__':
    print('\n WEEK 14 - Async Programming\n')
    
    asyncio.run(find_inefficiencies('bitcoin'))
    
    print('\n Complete!')