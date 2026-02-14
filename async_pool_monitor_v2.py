import asyncio
from web3 import AsyncWeb3
import time

# Retry Decorator
def async_retry(max_retries=3, delay=1):
    def decorator(func):
        async def wrapper (*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        print(f'⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...')
                        await asyncio.sleep(wait_time)
                    else:
                        print(f'❌ All {max_retries} attempts failed for {func.__name__}')
                        return None
        return wrapper
    return decorator

# Your Infura API key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet with ASYNC provider
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(infura_url))

# Uniswap V2 Pair ABI (minimal - just getReserves)
pair_abi = [
    {
        'constant': True,
        'inputs': [],
        'name': 'getReserves',
        'outputs': [
            {'name': 'reserve0', 'type': 'uint112'},
            {'name': 'reserve1', 'type': 'uint112'},
            {'name': 'blockTimestampLast', 'type': 'uint32'}
        ],
        'type': 'function'
    }
]

# ETH/USDC pool addresses
pools = {
    'Uniswap': '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
    'SushiSwap': '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0'
}

print('Async Web3 Version')
print('Pool Addresses:')
for name,address in pools.items():
    print(f'  {name}: {address}')

# TRUE ASYNC Reserve Reader
@async_retry(max_retries=3, delay=1)
async def get_pool_price(pool_name, pool_address):
    """Fetch reserves and calculate ETH price from a pool - TRUE ASYNC"""

    # Create contract instance
    pool_contract = web3.eth.contract(address=pool_address, abi=pair_abi)

    # Get reserves - TRUE ASYNC with await
    reserves = await pool_contract.functions.getReserves().call()

    # USDC is token0, WETH is toke1 in these pools
    usdc_reserves = reserves[0] / 10**6
    weth_reserves = reserves[1] / 10**18

    # Caculate ETH price
    eth_price = usdc_reserves / weth_reserves
    
    return {
        'pool': pool_name,
        'usdc_reserves': usdc_reserves,
        'weth_reserves': weth_reserves,
        'eth_price': eth_price
    }

async def monitor_pools():
    """Monitor multiple pools simultaneously - TRUE ASYNC"""

    print('📊\n Fetching reserves from multiple DEXs...\n')

    start_time = time.time()

    # Fetch from BOTH pools SIMULTANEOUSLY
    tasks = [
        get_pool_price('Uniswap', pools['Uniswap']),
        get_pool_price('SushiSwap', pools['SushiSwap'])
    ]

    results = await asyncio.gather(*tasks)

    end_time = time.time()
    fetch_time = end_time - start_time

    # Display results
    print('=' * 60)
    for result in results:
        print(f'\n{result["pool"]}:')
        print(f'  WETH Reserves: {result["weth_reserves"]:,.2f} ETH')
        print(f'  USDC Reserves: ${result["usdc_reserves"]:,.2f}')
        print(f'  ETH Price: ${result["eth_price"]:,.2f}')
    
    print(f'\n⏱ Fetch time: {fetch_time:.3f} seconds')
    print('=' * 60)

    return results

def detect_arbitrage(results):
    """Detect arb opportunities between pools"""

    print('\n🔍 ARB ANALYSIS:')
    print('=' * 60)
    
    # Extract prices
    prices = {result['pool']: result['eth_price'] for result in results}

    # find highest and lowest
    highest_pool = max(prices, key=prices.get)
    lowest_pool = min(prices, key=prices.get)

    highest_price = prices[highest_pool]
    lowest_price = prices[lowest_pool]

    # Caculate spread
    spread_usd = highest_price - lowest_price
    spread_percent = (spread_usd / lowest_price) * 100

    print(f'\n💰 Price Comparison:')
    for pool, price in prices.items():
        print(f' {pool}: ${price:,.2f}')

    print(f'\n📊 Arb Opportunity:')
    print(f'  Buy on: {lowest_pool} (${lowest_price:,.2f})')
    print(f'  Sell on: {highest_pool} (${highest_price:,.2f})')
    print(f'  Spread: ${spread_usd:.2f} ({spread_percent:.3f}%)')

    # Profitability check
    if spread_percent > 0.3:
        print(f'\n  ⚠️ Spread > 0.3% - might be profitable after gas!')
    else:
        print(f'\n  ❌ Spread too small (gas costs ~0.2-0.5%)')
    
    print('=' * 60)

async def continuous_monitor():
    """Run arbitrage detector continuously"""

    print('\n🔁 Starting continous monitoring (TRUE ASYNC)...')
    print('Press Ctrl+C to stop\n')

    check_count = 0

    try:
        while True:
            check_count += 1
            print(f'\n{"=" * 60}')
            print(f'CHECK #{check_count}')
            print(f'{"=" * 60}')

            # Run the monitor
            results = await monitor_pools()

            # Detect arbitrage
            if results:
                detect_arbitrage(results)

            # Wait 30 seconds before next check
            print('\n⏳ Next check in 30 seconds...')
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        print(f'\n\n⛔ Monitoring stopped by user')
        print(f'📊 Total checks performed: {check_count}')

# Run continuous monitoring
asyncio.run(continuous_monitor())