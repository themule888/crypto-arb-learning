from web3 import Web3

# Infura connection
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

if web3.is_connected():
    print('✅ Connected to Ethereum mainnet\n')
else:
    print('❌ Connection failed')
    exit()

# V3 pool ABI - slot0 gives us current price data
v3_pool_abi = [
    {
        'inputs': [],
        'name': 'slot0',
        'outputs': [
            {'name': 'sqrtPriceX96', 'type': 'uint160'},
            {'name': 'tick', 'type': 'int24'},
            {'name': 'observationIndex', 'type': 'uint16'},
            {'name': 'observationCardinality', 'type': 'uint16'},
            {'name': 'observationCardinalityNext', 'type': 'uint16'},
            {'name': 'feeProtocol', 'type': 'uint8'},
            {'name': 'unlocked', 'type': 'bool'}
        ],
        'stateMutability': 'view',
        'type': 'function'
    },
    {
        'inputs': [],
        'name': 'liquidity',
        'outputs': [{'name': '', 'type': 'uint128'}],
        'stateMutability': 'view',
        'type': 'function'
    },
    {
        'inputs': [],
        'name': 'token0',
        'outputs': [{'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function'
    },
    {
        'inputs': [],
        'name': 'token1',
        'outputs': [{'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function'
    },
    {
        'inputs': [],
        'name': 'fee',
        'outputs': [{'name': '', 'type': 'uint24'}],
        'stateMutability': 'view',
        'type': 'function'
    }
]

# ========== V3 POOLS ==========
# ETH/USDC on Uniswap V3 (two fee tiers)
V3_POOLS = {
    'V3_0.05%': '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640',
    'V3_0.3%':  '0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8',
}

# ========== V2 POOLS ==========
V2_POOLS = {
    'Uniswap_V2': '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
    'SushiSwap':  '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0',
}

# V2 pair ABI (same as before)
v2_pair_abi = [
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

# Token decimals
USDC_DECIMALS = 6
WETH_DECIMALS = 18

def decode_v3_price(sqrtPriceX96, token0_is_usdc):
    """
    COnvert sqrtPriceX96 to human-reable ETH price in USDC.

    sqrtPriceX96 = sqrt(price) * 2^96
    price = (sqrtPriceX96 / 2^96) ^ 2

    But 'price' here is token1/token0 in raw units.
    We need to adjust for decimals.
    """

    # Step 1: Get the raw price ratio
    price_raw = (sqrtPriceX96 / 2**96) ** 2

    # Step 2: Adjust for decimal difference
    if token0_is_usdc:
        # token0 = USDC, token1 = WETH
        # price_raw = WETH/USDC in raw units
        # We want USDC per ETH, so flip it and adjust decimals
        eth_price = (1 / price_raw) * (10**WETH_DECIMALS / 10**USDC_DECIMALS)
    else:
        # token0 = WETH, token1 = USDC
        # price_raw = USDC/WETH in raw units
        eth_price = price_raw * (10**WETH_DECIMALS / 10**USDC_DECIMALS)
    
    return eth_price

def read_v3_pool(pool_name, pool_address):
    """Read price from a Uniswap V3 pool using slot0"""
    try:
        contract = web3.eth.contract(address=pool_address, abi=v3_pool_abi)

        # Get slot0 data
        slot0 = contract.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        tick = slot0[1]

        # Get current liquidity
        liquidity = contract.functions.liquidity().call()

        # Get fee tier
        fee = contract.functions.fee().call()

        # Check token order
        token0 = contract.functions.token0().call()

        # USDC address
        usdc_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        token0_is_usdc = token0.lower() == usdc_address.lower()

        # Decode price
        eth_price = decode_v3_price(sqrtPriceX96, token0_is_usdc)

        return {
            'pool': pool_name,
            'eth_price': eth_price,
            'sqrtPriceX96': sqrtPriceX96,
            'tick': tick,
            'liquidity': liquidity,
            'fee': fee / 10000,
            'success': True
        }
    
    except Exception as e:
        return {'pool': pool_name, 'success': False, 'error': str(e)}

def read_v2_pool(pool_name, pool_address):
    """Read price from a V2 pool"""
    try:
        contract = web3.eth.contract(address=pool_address, abi=v2_pair_abi)
        reserves = contract.functions.getReserves().call()

        # Token0 = USDC, Toke1 = WETH for both these pools
        usdc_reserves = reserves[0] / 10**USDC_DECIMALS
        weth_reserves = reserves[1] / 10**WETH_DECIMALS
        eth_price = usdc_reserves / weth_reserves
        
        return {
            'pool': pool_name,
            'eth_price': eth_price,
            'usdc_reserves': usdc_reserves,
            'weth_reserves': weth_reserves,
            'success': True
        }

    except Exception as e:
        return {'pool': pool_name, 'success': False, 'error': str(e)}
    
def main():
    """Read V3 and V2 pools, compare prices, detect spread"""

    print('📊 Uniswap V3 Pool Reader')
    print('=' * 60)

    all_prices = {}

    # Read V3 pools
    print('\n🔷 V3 Pools (Concentraded Liquidity):')
    print('-' * 60)

    for pool_name, pool_address in V3_POOLS.items():
        result = read_v3_pool(pool_name, pool_address)

        if result['success']:
            print(f'  {result["pool"]:12} ${result["eth_price"]:>10,.2f}')
            print(f'    {"":12}: tick: {result["tick"]} fee: {result["fee"]}%')
            print(f'    {"":12} liquidity: {result["liquidity"]:,}')
            all_prices[pool_name] = result['eth_price']
            
        else:
            print(f'   {result["pool"]:12} ❌ {result["error"][:40]}')

    # READ V2 pools
    print('\n🔶 V2 Pools (Constant Product):')
    print('-' * 60)

    for pool_name, pool_address in V2_POOLS.items():
        result = read_v2_pool(pool_name, pool_address)

        if result['success']:
            print(f'  {result["pool"]:12} ${result["eth_price"]:>10,.2f}')
            print(f'    {"":12} WETH: {result["weth_reserves"]:,.2f} USDC: ${result["usdc_reserves"]:,.0f}')
            all_prices[pool_name] = result['eth_price']
        else:
            print(f'  {result["pool"]:12} ❌ {result["error"][:40]}')

        # Find Spreads
    if len(all_prices) >=2:
        print('\n📊 SPREAD ANALYSIS (V2 vs V3):')
        print('=' * 60)

        highest_pool = max(all_prices, key=all_prices.get)
        lowest_pool = min(all_prices, key=all_prices.get)

        highest_price = all_prices[highest_pool]
        lowest_price = all_prices[lowest_pool]

        spread_usd = highest_price - lowest_price
        spread_pct = (spread_usd / lowest_price) * 100

        print(f'  Highest: {highest_pool:12} ${highest_price:,.2f}')
        print(f'  Lowest:  {lowest_pool:12} ${lowest_price:,.2f}')
        print(f'  Spread:  ${spread_usd:.2f} ({spread_pct:.4f}%)')

        # Check if spread is cross-version (V2 vs V3)
        v2_names = set(V2_POOLS.keys())
        v3_names = set(V3_POOLS.keys())

        if (highest_pool in v2_names and lowest_pool in v3_names) or \
            (highest_pool in v3_names and lowest_pool in v2_names):
                print(f'  ⚡️ CROSS-VERSION spread (V2 vs V3)!')
        else:
                print(f'  ℹ️ Same-version spread')

            # Show all pairwise spreads
        print(f'\n All pairwise spreads:')
        pool_names = list(all_prices.keys())
        for i in range(len(pool_names)):
            for j in range(i + 1, len(pool_names)):
                name_a = pool_names[i]
                name_b = pool_names[j]
                price_a = all_prices[name_a]
                price_b = all_prices[name_b]
                pair_spread = abs(price_a - price_b)
                pair_pct = (pair_spread / min(price_a, price_b)) * 100
                print(f'   {name_a} vs {name_b}: ${pair_spread:.2f} ({pair_pct:.4f}%)')

main()



