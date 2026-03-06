import asyncio
from web3 import AsyncWeb3
from datetime import datetime
import time

# Infura connection
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(infura_url))

# Configuration
MIN_SPREAD_PCT = 0.05
SCAN_INTERVAL = 15
GAS_COST_USD = 15.00

# V3 pool ABI
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
        'name': 'fee',
        'outputs': [{'name': '', 'type': 'uint24'}],
        'stateMutability': 'view',
        'type': 'function'
    }
]

# V2 pair ABI
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

USDC_DECIMALS = 6
WETH_DECIMALS = 18

POOLS = {
    'V3_0.05%':   ('0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640', 'v3'),
    'V3_0.3%':    ('0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8', 'v3'),
    'Uniswap_V2': ('0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc', 'v2'),
    'SushiSwap':  ('0x397FF1542f962076d0BFE58eA045FfA2d347ACa0', 'v2'),
}

POOL_CACHE = {}

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
                        print(f'  ⚠️Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...')
                        await asyncio.sleep(wait_time)
                    else:
                        print(f'  ❌ All {max_retries} attempts failed for {func.__name__}')
                        return None
        return wrapper
    return decorator

def decode_v3_price(sqrtPriceX96, token0_is_usdc):
    """Convert sqrtPriceX96 to human-readable ETH price in USDC"""
    price_raw = (sqrtPriceX96 / 2**96) ** 2

    if token0_is_usdc:
        eth_price = (1 / price_raw) * (10**WETH_DECIMALS / 10**USDC_DECIMALS)
    else:
        eth_price = price_raw * (10**WETH_DECIMALS / 10**USDC_DECIMALS)
    
    return eth_price

async def cache_static_data():
    """Fetch token0 and fee once for all v3 pools - these never change"""
    usdc_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

    for pool_name, pool_data in POOLS.items():
        if pool_data[1] == 'v3':
            contract = web3.eth.contract(address=pool_data[0], abi=v3_pool_abi)
            token0 = await contract.functions.token0().call()

            POOL_CACHE[pool_name] = {
                'token0_is_usdc': token0.lower() == usdc_address.lower(),
            }
            print(f'  ✅ Cahced {pool_name}')
    print()


@async_retry(max_retries=3, delay=1)
async def read_pool(pool_name, pool_address, version):
    """Read ETH price - optimized with cache and parallel calls"""
    if version == 'v3':
        contract = web3.eth.contract(address=pool_address, abi=v3_pool_abi)

        # Fetch slot0 and liquiditiy SIMULTANEOUSLY
        slot0, liquidity = await asyncio.gather(
            contract.functions.slot0().call(),
            contract.functions.liquidity().call()
        )

        sqrtPriceX96 = slot0[0]
        tick = slot0[1]

        # Use cached token0 instead of fetching every time
        token0_is_usdc = POOL_CACHE[pool_name]['token0_is_usdc']
        eth_price = decode_v3_price(sqrtPriceX96, token0_is_usdc)

        return {
            'pool': pool_name,
            'version': 'v3',
            'eth_price': eth_price,
            'tick': tick,
            'liquidity': liquidity,
            'success': True
        }

    else:
        contract = web3.eth.contract(address=pool_address, abi=v2_pair_abi)
        reserves = await contract.functions.getReserves().call()

        usdc_reserves = reserves[0] / 10**USDC_DECIMALS
        weth_reserves = reserves[1] / 10**WETH_DECIMALS
        eth_price = usdc_reserves / weth_reserves

        return {
            'pool': pool_name,
            'version': 'v2',
            'eth_price': eth_price,
            'usdc_reserves': usdc_reserves,
            'weth_reserves': weth_reserves,
            'success': True
        }
    
def find_best_arb(prices):
    """Compare all pools pairwise, find best spread"""
    if len(prices) < 2:
        return None
    
    best_arb = None
    best_spread_pct = 0

    pool_names = list(prices.keys())

    for i in range(len(pool_names)):
        for j in range(i + 1, len(pool_names)):
            name_a = pool_names[i]
            name_b = pool_names[j]

            price_a = prices[name_a]['eth_price']
            price_b = prices[name_b]['eth_price']

            version_a = prices[name_a]['version']
            version_b = prices[name_b]['version']

            spread_usd = abs(price_a - price_b)
            spread_pct = (spread_usd / min(price_a, price_b)) * 100

            is_cross = version_a != version_b

            if price_a < price_b:
                buy_pool = name_a
                sell_pool = name_b
                buy_price = price_a
                sell_price = price_b
            else:
                buy_pool = name_b
                sell_pool = name_a
                buy_price = price_b
                sell_price = price_a
            
            if spread_pct > best_spread_pct:
                best_spread_pct = spread_pct
                best_arb = {
                    'buy_pool': buy_pool,
                    'sell_pool': sell_pool,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'spread_usd': spread_usd,
                    'spread_pct': spread_pct,
                    'is_cross': is_cross,
                    'profitable': spread_usd > GAS_COST_USD,
                }
    return best_arb

async def scan_all_pools():
    """Read all pools SIMULTANEOUSLY with asyncio.gather"""
    tasks = [
        read_pool(pool_name, pool_data[0], pool_data[1])
        for pool_name, pool_data, in POOLS.items()
    ]

    results = await asyncio.gather(*tasks)

    prices = {}
    for result in results:
        if result is not None and result ['success']:
            prices[result['pool']] = result
        elif result is None:
            print(f'  ❌ A pool failed all retries')

    return prices

async def main():
    """Continuous async monitoring loop"""
    print('🤖 V3 vs V2 ARB DETECTOR (ASYNC)')
    print(f'  Min spread: {MIN_SPREAD_PCT}%')
    print(f'  Gas estimate: ${GAS_COST_USD}')
    print(f'  Scan every: {SCAN_INTERVAL}s')
    print(f'  Pools: {len(POOLS)}')
    print('=' * 60)

    await cache_static_data()


    scan_count = 0

    try:
        while True:
            scan_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            print(f'\n[{timestamp}] Scan #{scan_count}')
            print('-' * 60)

            start = time.time()
            prices = await scan_all_pools()
            fetch_time = time.time() - start

            for name, data in prices.items():
                if data['version'] == 'v3':
                    print(f'  {name:12} ${data["eth_price"]:>10,.2f}  (tick: {data["tick"]})')
                else:
                    print(f'  {name:12} ${data["eth_price"]:>10,.2f}  (V2)')

            arb = find_best_arb(prices)

            if arb and arb ['spread_pct'] >= MIN_SPREAD_PCT:
                cross_tag = '⚡️CROSS' if arb['is_cross'] else '  SAME'
                profit_tag = '💰 PROFITABLE' if arb['profitable'] else '❌ Gas > spread'

                print(f'\n  {cross_tag} | Buy: {arb["buy_pool"]} ${arb["buy_price"]:,.2f}')
                print(f'         | Sell: {arb["sell_pool"]} ${arb["sell_price"]:,.2f}')
                print(f'         | Spread: ${arb["spread_usd"]:.2f} ({arb["spread_pct"]:.4f}%)')
                print(f'         | {profit_tag}')

            else:
                print(f'\n  No spreads above {MIN_SPREAD_PCT}%')

            print(f'\n  ⏱ Fetch: {fetch_time:.3f}s')
            print('=' * 60)

            await asyncio.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print(f'\n\n⛔ Stopped after {scan_count} scans')


asyncio.run(main())

