import asyncio
from web3 import AsyncWeb3
import time

# Retry Decorator
def async_retry(max_retries=3, delay=1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range (max_retries):
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

# WEBSOCKET connection (not HTTP!)
ws_url = f'wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}'
web3 = AsyncWeb3(AsyncWeb3.WebocketProvider(ws_url))

# Uniswap V2 Pair ABI
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

print('🔌 WebSocket Version')
print('Pool Addresses:')
for name, address in pools.items():
    print(f'  {name}: {address}')

# TRUE ASYNC Reserve Reader (same as before)
@async_retry(max_retries=3, delay=1)
async def get_pool_price(pool_name, pool_address):
    """Fetch Reserves and calculate ETH price from a pool"""

    pool_contract = web3.eth.contract(address=pool_address, abi=pair_abi)
    reserves = await pool_contract.functions.getReserves().call()

    usdc_reserves = reserves[0] / 10**6
    weth_reserves = reserves[1] / 10**18
    eth_price= usdc_reserves / weth_reserves

    return {
        'pool': pool_name,
        'usdc_reserves': usdc_reserves,
        'weth_reserves': weth_reserves,
        'eth_price': eth_price
    }

async def monitor_pools():
    """Monitor mulitple pools simultaneuously"""

    start_time = time.time()

    tasks = [
        get_pool_price('Uniswap', pools['Uniswap']),
        get_pool_price('SushiSwap', pools['SushiSwap'])
    ]

    results = await asyncio.gather(*tasks)
    fetch_time = time.time() - start_time

    # Display results
    print('=' * 60)
    for result in results:
        print(f'{result["pool"]}: ${result["eth_price"]:,.2f}')
    
    print(f'⏱ Fetch: {fetch_time:.3f}s')

    # Quick arb check
    prices = {r['pool']: r['eth_price'] for r in results}
    spread = abs(prices['Uniswap'] - prices['SushiSwap'])
    spread_pct = (spread / min(prices.values())) * 100

    if spread_pct > 0.1:
        print(f'💰 Spread: ${spread:.2f} ({spread_pct:.3f}%)')
    
    print('=' * 60)

async def watch_blocks():
    """Subscribe to new blocks and monitor on each one"""

    print(f'\n🔔 Subscribing to new blocks...')
    print('Updates every ~12 seconds (each block)')
    print('Press Ctrl+C to stop\n')

    block_count = 0

    try:
        # Subscribe to new block headers
        subscription_id = await web3.eth.subscribe('newHeads')

        async for block in web3.eth.get_subscription_events(subscription_id):
            block_count += 1

            print(f'\n🆕 Block #{block["number"]} (Check #{block_count})')

            # Monitor pools on this block
            await monitor_pools()
    
    except KeyboardInterrupt:
        print(f'\n\n⛔️ Monitoring stopped')
        print(f'📊 Blocks monitored: {block_count}')
    
# Run Block watcher
asyncio.run(watch_blocks())