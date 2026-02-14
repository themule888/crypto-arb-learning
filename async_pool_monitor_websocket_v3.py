import asyncio
from web3 import AsyncWeb3
import time

# Retry Decorator
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
                        print(f'⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...')
                        await asyncio.sleep(wait_time)
                    else:
                        print(f'❌ All {max_retries} attempts failed for {func.__name__}')
                        return None
        return wrapper
    return decorator

# Your Infura API key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# WEBSOCKET connection
ws_url = f'wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}'

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
    'Uniswap_V2': '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
    'SushiSwap': '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0',
    'Fraxswap': '0x92C7b5Ce4cb0e5483F3365C1449f21578eE9f21A',
}

print('🔌 WebSocket Version (Web3.py 7.14.1)')

@async_retry(max_retries=3, delay=1)
async def get_pool_price(web3, pool_name, pool_address):
    """Fetch reserves and calculate ETH price"""
    pool_contract = web3.eth.contract(address=pool_address, abi=pair_abi)
    reserves = await pool_contract.functions.getReserves().call()
    
    usdc_reserves = reserves[0] / 10**6
    weth_reserves = reserves[1] / 10**18
    eth_price = usdc_reserves / weth_reserves
    
    return {'pool': pool_name, 'eth_price': eth_price}

async def monitor_pools(web3):
    """Monitor pools with full arb analysis"""
    start = time.time()
    
    # Fetch from ALL pools simultaneuosly
    tasks = [
        get_pool_price(web3, pool_name, pool_address)
        for pool_name, pool_address in pools.items()
    ]

    results= await asyncio.gather(*tasks, return_exceptions=True)
    fetch_time = time.time() - start

    # Filter out failed pools
    successful = [r for r in results if isinstance(r, dict)]

    if not successful:
        print('❌ All pools failed')
        return
    
    print('=' * 60)
    for r in successful:
        print(f'{r["pool"]:15} ${r["eth_price"]:,.2f}')

    
    # ARB ANALYSIS
    prices = {r['pool']: r['eth_price'] for r in successful}
    highest_pool = max(prices, key=prices.get)
    lowest_pool = min(prices, key=prices.get)
    
    highest_price = prices[highest_pool]
    lowest_price = prices[lowest_pool]
    
    spread_usd = highest_price - lowest_price
    spread_pct = (spread_usd / lowest_price) * 100
    
    print(f'\n💰 Arbitrage:')
    print(f'  Buy:  {lowest_pool} @ ${lowest_price:,.2f}')
    print(f'  Sell: {highest_pool} @ ${highest_price:,.2f}')
    print(f'  Spread: ${spread_usd:.2f} ({spread_pct:.3f}%)')
    
    if spread_pct > 0.3:
        print(f'  ⚠️  PROFITABLE after gas!')
    else:
        print(f'  ❌ Too small (gas ~0.2-0.5%)')
    
    print(f'\n⏱  Fetch: {fetch_time:.3f}s | Pools: {len(successful)}/{len(pools)}')
    print('=' * 60)

async def watch_blocks():
    """Watch new blocks via WebSocket - POLLING APPROACH"""
    
    print('\n🔔 Starting block monitor...\n')
    
    # Create provider and web3
    provider = AsyncWeb3.WebSocketProvider(ws_url)
    web3 = AsyncWeb3(provider)
    
    # Connect
    await web3.provider.connect()
    print('✅ Connected!')
    print('Checking for new blocks every 12 seconds...\n')
    
    block_count = 0
    last_block = 0
    
    try:
        while True:
            # Get latest block number
            current_block = await web3.eth.block_number
            
            # If new block found
            if current_block > last_block:
                block_count += 1
                print(f'\n🆕 Block #{current_block} (Check #{block_count})')
                
                # Monitor pools
                await monitor_pools(web3)
                
                last_block = current_block
            
            # Wait 12 seconds before next check
            await asyncio.sleep(12)
            
    except KeyboardInterrupt:
        print(f'\n\n⛔ Stopped')
        print(f'📊 Blocks monitored: {block_count}')
    
    finally:
        await web3.provider.disconnect()
        print('Disconnected')

# Run it
asyncio.run(watch_blocks())