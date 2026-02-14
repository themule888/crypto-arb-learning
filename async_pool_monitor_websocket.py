import asyncio
from web3 import AsyncWeb3
import time
import json

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
    'Uniswap': '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
    'SushiSwap': '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0'
}

async def get_pool_price(web3, pool_name, pool_address):
    """Fetch reserves and calculate ETH price"""
    pool_contract = web3.eth.contract(address=pool_address, abi=pair_abi)
    reserves = await pool_contract.functions.getReserves().call()
    
    usdc_reserves = reserves[0] / 10**6
    weth_reserves = reserves[1] / 10**18
    eth_price = usdc_reserves / weth_reserves
    
    return {'pool': pool_name, 'eth_price': eth_price}

async def monitor_pools(web3):
    """Monitor pools"""
    start = time.time()
    
    results = await asyncio.gather(
        get_pool_price(web3, 'Uniswap', pools['Uniswap']),
        get_pool_price(web3, 'SushiSwap', pools['SushiSwap'])
    )
    
    fetch_time = time.time() - start
    
    print('=' * 60)
    for r in results:
        print(f'{r["pool"]}: ${r["eth_price"]:,.2f}')
    
    prices = {r['pool']: r['eth_price'] for r in results}
    spread = abs(prices['Uniswap'] - prices['SushiSwap'])
    spread_pct = (spread / min(prices.values())) * 100
    
    if spread_pct > 0.1:
        print(f'💰 Spread: ${spread:.2f} ({spread_pct:.3f}%)')
    
    print(f'⏱ Fetch: {fetch_time:.3f}s')
    print('=' * 60)

async def watch_blocks():
    """Watch new blocks via WebSocket"""
    
    print('🔌 Connecting to Ethereum WebSocket...\n')
    
    async with AsyncWeb3.persistent_websocket(
        AsyncWeb3.WebSocketProvider(ws_url)
    ) as web3:
        
        print('✅ WebSocket connected!')
        print('Subscribing to new blocks...\n')
        
        block_count = 0
        
        try:
            async for block in web3.eth.subscribe('newHeads'):
                block_count += 1
                block_number = block['number']
                
                print(f'\n🆕 Block #{block_number} (Check #{block_count})')
                await monitor_pools(web3)
                
        except KeyboardInterrupt:
            print(f'\n\n⛔ Stopped')
            print(f'📊 Blocks: {block_count}')

# Run it
asyncio.run(watch_blocks())