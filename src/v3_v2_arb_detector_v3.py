import asyncio
from web3 import AsyncWeb3
from functools import wraps
import time

# Retry deocrator

def async_retry(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries -1:
                        raise
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

INFURA_URL = "https://mainnet.infura.io/v3/af63bf5e933b419b9f96b021ce430232"

w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(INFURA_URL))

POOLS = {
    "V3_005": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
    "V3_030": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
    "V2_UNI": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
    "V2_SUSHI": "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"
}

USDC_DECIMALS = 6
WETH_DECIMALS = 18
GAS_COST_USD = 15.00
SCAN_INTERVALS = 15

def calc_v2_output(amount_in_usd, reserves_usdc, reserves_weth, eth_price, buy=True):
    """
    Calculate exact output for a V2 swap including price impact.

    buy=True: spending USDC to buy WETH
    buy=False: selling WETH for usdc
    """
    if buy:
        # Buying ETH: put in USDC, get out WETH
        amount_in = amount_in_usd # Already in USDC terms
        reserves_in = reserves_usdc
        reserves_out = reserves_weth
    else:
        # Selling ETH: put in WETH, get out USDC
        amount_in = amount_in_usd / eth_price # Convert USD to WETH amount
        reserves_in = reserves_weth
        reserves_out = reserves_usdc

    # Constant product with 0.3% fee
    amount_in_with_fee = amount_in * 997
    numerator = reserves_out * amount_in_with_fee
    denominator = (reserves_in * 1000) + amount_in_with_fee
    amount_out = numerator / denominator

    if buy:
        # Got WETH back, convert USD value
        value_out = amount_out * eth_price
    else: 
        # Got USDC back, already in USD
        value_out = amount_out

    return {
        'amount_out': amount_out,
        'value_out_usd': value_out,
        'price_impact_usd': amount_in_usd - value_out,
        'effective_price': amount_in_usd / amount_out if buy else value_out / (amount_in_usd / eth_price)
    }

def calc_v3_output(amount_in_usd, liquidity, sqrt_price_x96, fee_tier, eth_price, buy=True):
    """
    Calculate V3 swap output using current tick liquidity.
    Simplified model - assumes trade stays within current tick range.
    Works in sqrtPriceX96 space to avoid floating point issues.
    """
    Q96 = 2 ** 96
    fee_multiplier = 1 - (fee_tier / 1_000_000)

    if buy:
        # Buying ETH with USDC — token0 in, token1 out
        amount_in_raw = amount_in_usd * (10 ** USDC_DECIMALS)
        amount_in_after_fee = amount_in_raw * fee_multiplier

        # New sqrtPrice after pushing token0 in:
        # new_sqrtP = sqrtP * L / (L + amount_in * sqrtP / Q96)
        L = liquidity
        sqrtP = sqrt_price_x96
        new_sqrt_price_x96 = (sqrtP * L) / (L + amount_in_after_fee * sqrtP / Q96)

        # Token1 (WETH) output = L * (sqrtP - new_sqrtP) / Q96
        amount_out_raw = L * (sqrtP - new_sqrt_price_x96) / Q96
        amount_out = amount_out_raw / (10 ** WETH_DECIMALS)
        value_out = amount_out * eth_price

    else:
        # Selling ETH for USDC — token1 in, token0 out
        amount_in_eth = amount_in_usd / eth_price
        amount_in_raw = amount_in_eth * (10 ** WETH_DECIMALS)
        amount_in_after_fee = amount_in_raw * fee_multiplier

        # New sqrtPrice after pushing token1 in:
        # new_sqrtP = sqrtP + amount_in * Q96 / L
        L = liquidity
        sqrtP = sqrt_price_x96
        new_sqrt_price_x96 = sqrtP + (amount_in_after_fee * Q96 / L)

        # Token0 (USDC) output = L * (new_sqrtP - sqrtP) / Q96  ... but need to divide by price
        # Actually: token0 out = L * (1/sqrtP - 1/new_sqrtP) * Q96
        amount_out_raw = L * Q96 * (1/sqrtP - 1/new_sqrt_price_x96)
        amount_out = amount_out_raw / (10 ** USDC_DECIMALS)
        value_out = amount_out

    return {
        'amount_out': amount_out,
        'value_out_usd': value_out,
        'price_impact_usd': amount_in_usd - value_out,
        'effective_price': amount_in_usd / amount_out if buy else value_out / (amount_in_usd / eth_price)
    }

def find_optimal_trade(buy_pool, sell_pool, trade_sizes=None):
    """
    Test increasing trade sizes to find maximum profit.

    buy_pool: dict with pool data (version, eth_price, + reserves or liquidity/sqrt_price)
    sell_pool: dict with pool data
    """
    if trade_sizes is None:
        trade_sizes = [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
    
    best_profit = 0
    best_size = 0
    results = []

    for size in trade_sizes:
        # Step 1: Buy ETH on cheap pool
        if buy_pool['version'] == 'v2':
            buy_result = calc_v2_output(
                size, buy_pool['reserves_usdc'], buy_pool['reserves_weth'],
                buy_pool['eth_price'], buy=True
            )
        else:
            buy_result = calc_v3_output(
                size, buy_pool['liquidity'], buy_pool['sqrt_price_x96'],
                buy_pool['fee_tier'], buy_pool['eth_price'], buy=True
            )
        
        eth_bought = buy_result['amount_out']

        # Step 2: Sell that ETH on expensive pool
        sell_value_usd = eth_bought * sell_pool['eth_price']

        if sell_pool['version'] == 'v2':
            sell_result = calc_v2_output(
                sell_value_usd, sell_pool['reserves_usdc'], sell_pool['reserves_weth'],
                sell_pool['eth_price'], buy=False
            )
        else:
            sell_result = calc_v3_output(
                sell_value_usd, sell_pool['liquidity'], sell_pool['sqrt_price_x96'],
                sell_pool['fee_tier'], sell_pool['eth_price'], buy=False
            )

        # Step 3: Calculation profit
        revenue = sell_result['value_out_usd']
        profit = revenue - size - GAS_COST_USD

        results.append({
            'trade_size': size,
            'eth_bought': eth_bought,
            'revenue': revenue,
            'profit': profit,
            'buy_impact': buy_result['price_impact_usd'],
            'sell_impact': sell_result['price_impact_usd']
        })

        if profit > best_profit:
            best_profit = profit
            best_size = size

    return {
        'best_size': best_size,
        'best_profit': best_profit,
        'all_results': results
    }

V3_ABI = [
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
        'name': 'fee',
        'outputs': [{'name': '', 'type': 'uint24'}],
        'stateMutability': 'view',
        'type': 'function'
    }
]

V2_ABI = [
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

FEE_TIERS = {
    'V3_005': 500,
    'V3_030': 3000
}

@async_retry(max_retries=3, delay=1)
async def read_pool_data(pool_name, pool_address):
    """ Fetch all data the optimizer needs from a single pool."""

    if pool_name.startswith('V3'):
        contract = w3.eth.contract(address=pool_address, abi=V3_ABI)

        slot0, liquidity = await asyncio.gather(
            contract.functions.slot0().call(),
            contract.functions.liquidity().call()
        )

        sqrt_price_x96 = slot0[0]
        price_raw = (sqrt_price_x96 / 2**96) ** 2
        eth_price = (1 / price_raw) * (10**WETH_DECIMALS / 10**USDC_DECIMALS)

        return {
            'pool': pool_name,
            'version': 'v3',
            'eth_price': eth_price,
            'sqrt_price_x96': sqrt_price_x96,
            'liquidity': liquidity,
            'fee_tier': FEE_TIERS[pool_name]
        }
    
    else:
        contract = w3.eth.contract(address=pool_address, abi=V2_ABI)
        reserves = await contract.functions.getReserves().call()

        reserves_usdc = reserves[0] / 10**USDC_DECIMALS
        reserves_weth = reserves[1] / 10**WETH_DECIMALS
        eth_price = reserves_usdc / reserves_weth
        
        return {
            'pool': pool_name,
            'version': 'v2',
            'eth_price': eth_price,
            'reserves_usdc': reserves_usdc,
            'reserves_weth': reserves_weth
        }

async def main():
    """Continuous monitoring with trade size optimization"""
    print(f'🔧 TRADE SIZE OPTIMIZIER (CONTINUOUS)')
    print(f'  Gas estimate: ${GAS_COST_USD}')
    print(f'  Scan every: {SCAN_INTERVALS}s')
    print(f'  Pools: {len(POOLS)}')
    print('=' * 60)

    scan_count = 0

    try: 
        while True:
            scan_count +=1
            timestamp = time.strftime('%H:%M:%S')
            print(f'\n[{timestamp}] Scan #{scan_count}')
            print('-' * 60)

            # Fetch all pools in parallel
            start = time.time()
            tasks = [
                read_pool_data(name, address)
                for name, address in POOLS.items()
            ]
            results = await asyncio.gather(*tasks)
            fetch_time = time.time() - start

            # Build price dict, skip failures
            pools = {}
            for result in results:
                if result is not None:
                    pools[result['pool']] = result
            
            # Display prices
            for name, data in pools.items():
                print(f'  {name:12} ${data["eth_price"]:>10,.2f}')

            # Test all pair combinations
            best_overall = None
            pool_names = list(pools.keys())

            for i in range(len(pool_names)):
                for j in range(len(pool_names)):
                    if i == j:
                        continue

                    buy_name = pool_names[i]
                    sell_name = pool_names[j]
                    buy_pool = pools[buy_name]
                    sell_pool = pools[sell_name]

                    if buy_pool['eth_price'] >= sell_pool['eth_price']:
                        continue

                    optimal = find_optimal_trade(buy_pool, sell_pool)

                    if best_overall is None or optimal['best_profit'] > best_overall['profit']:
                        best_overall = {
                            'buy': buy_name,
                            'sell': sell_name,
                            'profit': optimal['best_profit'],
                            'size': optimal['best_size'],
                            'spread': sell_pool['eth_price'] - buy_pool['eth_price']
                        }
            
            # Display result
            if best_overall and best_overall['profit'] > 0:
                print(f'\n  🚨PROFITABLE: Buy {best_overall["buy"]} -> Sell {best_overall["sell"]}')
                print(f'    Trade ${best_overall["size"]:,} for ${best_overall["profit"]:.2f} profit')
            else:
                print(f'\n  ⏳ Best: {best_overall["buy"]} -> {best_overall["sell"]}')
                print(f'   Spread: ${best_overall["spread"]:.2f} | No profitable size')

            print(f'  ⏱ Fetch: {fetch_time:.3f}s')
            print('=' * 60)

            await asyncio.sleep(SCAN_INTERVALS)

    except KeyboardInterrupt:
        print(f'\n\n⛔ Stopped after {scan_count} scans')

asyncio.run(main())