from web3 import Web3
import asyncio
import time

# Infura connection
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

if web3.is_connected():
    print('✅ Connected to Ethereum mainnet\n')
else:
    print('❌ Connection failed')
    exit()

# Minimal ABI - just getReserves (all we need)
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

# Pool List - ETH/USDC pairs across different DEXs
# Format: 'Name': ('address', usdc_is_token)
pools = {
    'Uniswap_V2': ('0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc', True),
    'SushiSwap':  ('0x397FF1542f962076d0BFE58eA045FfA2d347ACa0', True),
    'ShibaSwap':  ('0x20E95253e54490D8d30ea41574b24F741ee70201', True),
}

def get_pool_price(pool_name, pool_address, usdc_is_token0):
    """Read reserves from one pool and calculate ETH price"""
    try:
        # Create contract instance
        contract = web3.eth.contract(address=pool_address, abi=pair_abi)

        # Get reserves
        reserves = contract.functions.getReserves().call()

        # Assign reserves correctly absed on token order
        if usdc_is_token0:
            usdc_reserves = reserves[0] / 10**6
            weth_reserves = reserves[1] / 10**18
        else:
            weth_reserves = reserves[0] / 10**18
            usdc_reserves = reserves[1] / 10**6

        # Calculate ETH price
        eth_price = usdc_reserves / weth_reserves
        tvl = usdc_reserves * 2

        return {
            'pool': pool_name,
            'eth_price': eth_price,
            'tvl': tvl,
            'success': True
        }
    
    except Exception as e:
        return {
            'pool': pool_name,
            'success': False,
            'error': str(e)
        }
    
def scan_all_pools():
    """Scan all pools and rank be ETH price"""
    print('🔍 Scanning pools....\n')

    results = []

    for pool_name, pool_data in pools.items():
        pool_address = pool_data[0]
        usdc_is_token0 = pool_data[1]

        result = get_pool_price(pool_name, pool_address, usdc_is_token0)
        results.append(result)

     # Seperate successful and failed
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

     # Sort by ETH price (hights first)
    successful.sort(key=lambda x: x['eth_price'], reverse=True)

    # Display results
    print(f'{"Pool":<15} {"ETH Price":>12} {"TVL":>15}')
    print('-' * 45)

    for r in successful:
        print(f'{r["pool"]:<15} ${r["eth_price"]:>11,.2f} ${r["tvl"]:>14,.0f}')

    for r in failed:
        print(f'{r["pool"]:<15} FAILED: {r["error"][:30]}')

    return successful

def find_arb(successful):
    """Find best arb opportunity from scan results"""
    if len(successful) < 2:
        print('❌ Need at least 2 pools')
        return

    highest = successful[0]
    lowest = successful[-1]

    spread_usd = highest['eth_price'] - lowest['eth_price']
    spread_pct = (spread_usd /lowest['eth_price']) * 100

    print(f'\n📊 ARB Analysis:')
    print(f'  Buy on:  {lowest["pool"]} @ ${lowest["eth_price"]:,.2f}')
    print(f'  Sell on: {highest["pool"]} @ ${highest["eth_price"]:,.2f}')
    print(f'  Spread:  ${spread_usd:.2f} ({spread_pct:.4f}%)')

    if spread_pct > 0.5:
        print(f'  ⚡️ PROFTITABLE after gas!')
    else:
        print(f'  ❌ Too small (need >0.5% on mainnet)')

# Run it
results = scan_all_pools()
find_arb(results)
