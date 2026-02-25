from web3 import Web3
from datetime import datetime

# Infura connection
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

if web3.is_connected():
    print('✅ Connected to Ethereum mainnet\n')
else:
    print('❌ Connection failed')
    exit()

# Token addresses (checksummed)
TOKENS = {
    'WETH':  '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDC':  '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'WBTC':  '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'LINK':  '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    'UNI':   '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
}

# Minimal ABI - just getReserves and token0
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
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'token0',
        'outputs': [{'name': '', 'type': 'address'}],
        'type': 'function'
    }
]

# Pool addresses for each pair on each DEX
# Format: 'PAIR': {'DEX': 'address'}
POOLS = {
    'WBTC/WETH': {
        'Uniswap_V2': '0xBb2b8038a1640196FbE3e38816F3e67Cba72D940',
        'SushiSwap':  '0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58',
    },
    'LINK/WETH': {
        'Uniswap_V2': '0xa2107FA5B38d9bbd2C461D6EDf11B11A50F6b974',
        'SushiSwap':  '0xC40D16476380e4037e6b1A2594cAF6a6cc8Da967',
    },
    'UNI/WETH': {
        'Uniswap_V2': '0xd3d2E2692501A5c9Ca623199D38826e513033a17',
        'SushiSwap':  '0xDafd66636E2561b0284EDdE37e42d192F2844D40',
    },
}

# Token decimals
DECIMALS = {
    'WETH': 18,
    'USDC': 6,
    'WBTC': 8,
    'LINK': 18,
    'UNI': 18,
}

def get_price(pool_address, token_a, token_b):
    """
    Get price of token_a in terms of token_b from a pool.
    Returns price as a float, or None if failed.
    """
    try:
        contract = web3.eth.contract(address=pool_address, abi=pair_abi)

        # Get reserves and token order
        reserves = contract.functions.getReserves().call()
        token0_address = contract.functions.token0().call()

       # Figure out which reserve belongs to which token
        dec_a = DECIMALS[token_a]
        dec_b = DECIMALS[token_b]

        if token0_address.lower() == TOKENS[token_a].lower():
            #token_a is token0
            reserve_a = reserves[0] / 10**dec_a
            reserve_b = reserves[1] / 10**dec_b
        else:
            # token_a is token1
            reserve_a = reserves[1] / 10**dec_a
            reserve_b = reserves[0] / 10**dec_b
        
        # Price = how much token_b you get per token_a
        price = reserve_b / reserve_a
        tvl = reserve_b * 2 # Both sides equal value, so double one side
        return {'price': price, 'tvl': tvl}
    
    except Exception as e:
        print(f'  ❌ Error reading {pool_address[:10]} ...: {e}')
        return None

def scan_pair(pair_name, dex_pools):
    """Scan one token pair across all DEXs and find best spread"""

    # Parse pair name into two tokens
    token_a, token_b = pair_name.split('/')

    print(f'\n📊 {pair_name}')
    print('-' * 40)

    # Fetch price from each DEX
    prices = {}
    for dex_name, pool_address in dex_pools.items():
        result = get_price(pool_address, token_a, token_b)
        if result is not None:
            tvl = result['tvl']
            price = result['price']
            if tvl < 100: # Skip pools with less thank $100k TVL
                print(f'  {dex_name:12} ⚠️ TVL too low (${tvl:,.0f} {token_b})')
                continue
            prices[dex_name] = price
            print(f'  {dex_name:12} {price:.6f} {token_b} per {token_a} (TVL: {tvl:,.0f} {token_b})')
    
    # Need at least 2 DEXs to find a spread
    if len(prices) < 2:
        print(f'  ⚠️ Not enough data to compare')
        return None
    
    # Find best spread
    highest_dex = max(prices, key=prices.get)
    lowest_dex = min(prices, key=prices.get)

    highest_price = prices[highest_dex]
    lowest_price = prices[lowest_dex]

    spread_pct = ((highest_price - lowest_price) / lowest_price) * 100

    print(f'\n  Buy:    {lowest_dex} @ {lowest_price:.6f}')
    print(f'  Sell:   {highest_dex} @ {highest_price:.6f}')
    print(f'  Spread: {spread_pct:.4f}%')

    if spread_pct > 0.5:
        print(f'  ⚡️ POTENTIALLY PROFITABLE')
    else:
        print(f'  ❌ Too small')
    
    return {
        'pair': pair_name,
        'buy_dex': lowest_dex,
        'sell_dex': highest_dex,
        'spread_pct': spread_pct,
    }

def main():
    """Scan all paris and rank by spread"""
    print(f'🔍 Scanning {len(POOLS)} pairs across DEXs...')
    print(f'⏰ {datetime.now().strftime("%H:%M:%S")}\n')

    results = []

    for pair_name, dex_pools in POOLS.items():
        result = scan_pair(pair_name, dex_pools)
        if result is not None:
            results.append(result)

    # Rank by spread
    results.sort(key=lambda x: x['spread_pct'], reverse=True)

    print(f'\n{"=" * 50}')
    print(f'📈 RANKED BY SPREAD')
    print(f'{"=" * 50}')

    for r in results:
        print(f'{r["pair"]:12} {r["spread_pct"]:.4f}%  '
              f'Buy: {r["buy_dex"]}  Sell:{r["sell_dex"]}')

main()