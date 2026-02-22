# Pool Analyzer - Find Profitable Arb Opportunities
# Week 21 Session 2

from web3 import Web3

# Your Infura API key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check connection
if web3.is_connected():
    print('✅ Connected to Ethereum mainnet!\n')
else:
    print('❌ Connection failed')
    exit()

# Uniswap V2 Pair ABI (minimal)
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
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'token1',
        'outputs': [{'name': '', 'type': 'address'}],
        'type': 'function'
    }
]

def get_pool_reserves(pool_address):
    """
    Fetch reserves from a Uniswap V2 pool

    Args:
        pool_Address: Address of the pair contract

    Returns:
        dict with reserve0, reserve1, and token addresses
    """

    # Create contract instance
    pool_contract = web3.eth.contract(address=pool_address, abi=pair_abi)

    # Get reserves
    reserves = pool_contract.functions.getReserves().call()

    # Get token addresses
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()

    return {
        'reserve0': reserves[0],
        'reserve1': reserves[1],
        'token0': token0,
        'token1': token1
    }

def calculate_price_impact(reserve_in, reserve_out, amount_in):
    """
    CCalculate price impact percentage from a swap (with 0.3% fee)
    
    Args:
        reserve_in: Reserve of token being sold (in human-readable units)
        reserve_out: Reserve of token being bought (in human-readable units)
        amount_in: Amount being swapped (in human-readable units)
    
    Returns:
        impact_percent: Price impact as a percentage
    """

    # Price before swap
    price_before = reserve_out / reserve_in

    # Apply fee 0.3%
    amount_in_with_fee = amount_in * 0.997

    # Calculate new reserves
    new_reserve_in = reserve_in + amount_in_with_fee
    new_reserve_out = (reserve_in * reserve_out) / new_reserve_in

    # Price after swap
    price_after = new_reserve_out / new_reserve_in

    # Calculate impact
    impact_percent = ((price_before - price_after) / price_before) * 100

    return impact_percent

def calculate_swap_output_with_fee(reserve_in, reserve_out, amount_in):
    """
    Calculate swap output with Uniswap's 0.3% fee
    
    Args:
        reserve_in: Reserve of token being sold (in human-readable units)
        reserve_out: Reserve of token being bought (in human-readable units)
        amount_in: Amount of token being sold (in human-readable units)
    
    Returns:
        amount_out: Amount of token received (after fee)
    """
    # Apply 0.3% fee
    amount_in_with_fee = amount_in * 0.997

    # Constant product formula
    k = reserve_in * reserve_out
    new_reserve_in = reserve_in + amount_in_with_fee
    new_reserve_out = k / new_reserve_in
    amount_out = reserve_out - new_reserve_out

    return amount_out
    
def calculate_profitability(
        reserve_in_buy, reserve_out_buy,
        reserve_in_sell, reserve_out_sell,
        amount_in_usd, spread_percent, gas_price_gwei=30
):
    """
    Calculate if arb is profitable after ALL costs.

    Args:
        reserve_in_buy: USDC reserve on DEX where you BUY ETH
        reserve_out_buy: WETH reserve on DEX where you BUY ETH
        reserve_in_sell: WETH reserve on DEX where you SELL ETH
        reserve_out_sell: USDC reserve on DEX where you SELL ETH
        amount_in_usd: Amount to arbitrage (in USDC)
        spread_percent: Price difference between DEXs (%)
        gas_price_gwei: Current gas price in Gwei

    Returns:
        dict with profit breakdown
    """

    # Step 1: Buy ETH on cheaper DEX (swap USDC → ETH)
    eth_bought = calculate_swap_output_with_fee(reserve_in_buy, reserve_out_buy, amount_in_usd)

    # Step 2: Sell ETH on expensive DEX (swap ETH → USDC)
    usdc_received = calculate_swap_output_with_fee(reserve_in_sell, reserve_out_sell, eth_bought)

    # Calculate price impacts
    impact_buy = calculate_price_impact(reserve_in_buy, reserve_out_buy, amount_in_usd)
    impact_sell = calculate_price_impact(reserve_in_sell, reserve_out_sell, eth_bought)

    # Calculate gas cost
    # Flash loan arb typically uses ~250,000 gas
    gas_units = 250000
    gas_cost_eth = (gas_price_gwei * gas_units) / 10**9
    
    # Convert gas cost to USD using current pool price
    eth_price_usd = reserve_in_buy / reserve_out_buy
    gas_cost_usd = gas_cost_eth * eth_price_usd

    # Flash loan fee (Aave charges 0.09%)
    flash_loan_fee = amount_in_usd * 0.0009

    # Total costs
    total_costs = gas_cost_usd + flash_loan_fee

    # Profit calculation
    # Started with amount_in_usd USDC (borrowed via flash loan)
    # Ended with usdc_received USDC
    gross_profit = usdc_received - amount_in_usd
    net_profit = gross_profit - total_costs

    return {
        'usd_amount': amount_in_usd,
        'eth_bought': eth_bought,
        'usdc_received': usdc_received,
        'gross_profit': gross_profit,
        'gas_cost': gas_cost_usd,
        'flash_loan_fee': flash_loan_fee,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'impact_buy': impact_buy,
        'impact_sell': impact_sell,
        'profitable': net_profit > 0
    }

    # Test with real ETH/USDC pool
eth_usdc_pool = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'

print("=" * 60)
print("READING REAL UNISWAP V2 POOL")
print("=" * 60)

data = get_pool_reserves(eth_usdc_pool)

print(f"\nPool Address: {eth_usdc_pool}")
print(f"Token0: {data['token0']}")
print(f"Token1: {data['token1']}")
print(f"\nRaw Reserves:")
print(f"  Reserve0: {data['reserve0']:,}")
print(f"  Reserve1: {data['reserve1']:,}")

# Convert to human-readable (USDC = 6 decimals, WETH = 18 decimals)
# In this pool: token0 - USDC, token1 = WETH
usdc_reserves = data['reserve0'] / 10**6
weth_reserves = data['reserve1'] / 10**18

print(f'\nHuman-Reable:')
print(f'  USDC: ${usdc_reserves:,.2f}')
print(f'  WETH: {weth_reserves:,.2f} ETH')

# Calculate current price
eth_price = usdc_reserves / weth_reserves
print(f'\n Current ETH Price: ${eth_price:,.2f}')

# Calculate pool size (TVL)
tvl = usdc_reserves * 2 # Both sides worth the same amount
print(f'Total Value Locked (TVL): ${tvl:,.2f}')

print('=' * 60)

# Test different trade sizes on REAL pool
print(f'\n' + '=' * 60)
print(f'PRICE IMPACT ANALYSIS - REAL POOL')
print('=' * 60)

trade_sizes_eth = [0.1, 1.0, 10.0, 50.0, 100.0]

print(f'\nPool: {weth_reserves:,.2f} ETH / ${usdc_reserves:,.2f} USDC')
print(f'TVL: ${tvl:,.2f}')
print(f'Current Price: ${eth_price:,.2f} per ETH\n')

for eth_amount in trade_sizes_eth:
    # Calculate output
    usdc_out = calculate_swap_output_with_fee(weth_reserves, usdc_reserves, eth_amount)

    # Calculate price impact
    impact = calculate_price_impact(weth_reserves, usdc_reserves, eth_amount)

    # Effective price you got
    effective_price = usdc_out / eth_amount

    # Dollar value of trade
    trade_value = eth_amount * eth_price

    print(f"{eth_amount:6.1f} ETH (${trade_value:,.0f}) → ${usdc_out:,.2f} USDC")
    print(f'         Effective: ${effective_price:,.2f}/ETH | Impact: {impact:.4f}%\n')

print('=' * 60)

# Profitability Analysis
print("\n" + "=" * 60)
print("PROFITABILITY ANALYSIS (with Gas + Flash Loan Fee)")
print("=" * 60)

# Simulate two DEXs with 0.5% spread
# DEX A (cheaper): same as our real pool
# DEX B (expensive): 0.5% higher price

# Create "expensive DEX" reserves (0.5% higher price)
usdc_reserves_expensive = usdc_reserves * 1.005  # 0.5% more USDC per ETH
weth_reserves_expensive = weth_reserves

print(f"\nScenario: 0.5% spread between two DEXs")
print(f"DEX A Price: ${eth_price:,.2f}")
print(f"DEX B Price: ${eth_price * 1.005:,.2f}")
print(f"Spread: 0.5%")
print(f"\nGas Price: 30 Gwei (~$50-100 per transaction)\n")

trade_sizes = [1000.0, 5000.0, 10000.0, 25000.0, 50000.0]  # USDC amounts

for size in trade_sizes:
    result = calculate_profitability(
        usdc_reserves, weth_reserves,  # Buy ETH on DEX A (swap USDC → ETH)
        weth_reserves_expensive, usdc_reserves_expensive,  # Sell ETH on DEX B (swap ETH → USDC)
        size, 0.5, gas_price_gwei=30
    )
    
    print(f"${size:7,.0f} USDC Trade:")
    print(f"  ETH Bought:   {result['eth_bought']:.4f} ETH")
    print(f"  USDC Got:     ${result['usdc_received']:,.2f}")
    print(f"  Gross Profit: ${result['gross_profit']:7.2f}")
    print(f"  Gas Cost:     ${result['gas_cost']:7.2f}")
    print(f"  Flash Fee:    ${result['flash_loan_fee']:7.2f}")
    print(f"  Net Profit:   ${result['net_profit']:7.2f} {'✅ PROFITABLE' if result['profitable'] else '❌ LOSS'}")
    print(f"  Impact: {result['impact_buy']:.3f}% (buy) + {result['impact_sell']:.3f}% (sell)\n")