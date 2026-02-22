# AMM Calcultor - Understanding x*y=k
# Week 21 Session 1

def calculate_swap_output(reserve_in, reserve_out, amount_in):
    """"
    Calculare swap output using constant product from formula (no fee)

    Formula: x * y = k (constant)

    Args:
        reserve_in: Reserve of token being sold
        reserve_out: Reserve of token being bought
        amount_in: Amount of token being sold

    Returns:
        amount_out: Amount of token recieved
    """

    # Calculate k (the constant product)
    k = reserve_in * reserve_out

    # New reserve_in after adding input
    new_reserve_in = reserve_in + amount_in

    #Calculate new reserve_out (must maintain k)
    new_reserve_out = k / new_reserve_in

    # Amount out = difference between old and new reserve_out
    amount_out = reserve_out - new_reserve_out

    return amount_out


def calculate_swap_output_with_fee(reserve_in, reserve_out, amount_in, fee_percent=0.3):
    """
    Caclulate swap output with Uniswap's 0.3% fee

    Args:
        reserve_in: Reserve of token being sold
        reserve_out: Reserve of token being bought
        amount_in: Amount of token being sold
        fee_percent: Fee percentage (default 0.3 for UniSwap)
    
    Returns:
        amount_out: Amount of token recieved (after fee)
    """

    #Apply fee (0.3% mean you only get 99.7% of input into the swap)
    fee_multiplier = 1 - (fee_percent / 100)
    amount_in_with_fee = amount_in * fee_multiplier

    # Use the same formula as before, but with reduced input
    k = reserve_in * reserve_out
    new_reserve_in = reserve_in + amount_in_with_fee
    new_reserve_out = k / new_reserve_in
    amount_out = reserve_out - new_reserve_out

    return amount_out

# Example: ETH/USDC pool on Uniswap
print('=' * 60)
print('BASIC AMM CALCULATOR (No Fee)')
print('=' * 60)

# Pool reserves (from your uniswap_reader.py data)
eth_reserve = 100.0     #100 ETH
usdc_reserve = 300000.0  #300,000 USDC

print(f'  ETH Reserve: {eth_reserve:,.2f} ETH')
print(f'  USDC Reserve: ${usdc_reserve:,.2f}')
print(f'  k (constant): {eth_reserve * usdc_reserve:,.0f}')

# Current price
current_price = usdc_reserve / eth_reserve
print(f'  Current Price: ${current_price:,.2f} per ETH')

# Swap 1 ETH for USDC
amount_in = 1.0 # 1 ETH

usdc_out = calculate_swap_output(eth_reserve, usdc_reserve, amount_in)

print(f'\n--- Swap: {amount_in} ETH -> USDC ---')
print(f'  You recieve: ${usdc_out:,.2f} USDC')

# Calculate new reserves
new_eth_reserve = eth_reserve + amount_in
new_usdc_reserve = usdc_reserve - usdc_out

print(f'\nNew Pool State:')
print(f'  ETH Reserve:  {new_eth_reserve:,.2f} ETH')
print(f'  USDC Reserve: ${new_usdc_reserve:,.2f}')
print(f'  k (constant): {new_eth_reserve * new_usdc_reserve:,.0f}')

# New Price
new_price = new_usdc_reserve / new_eth_reserve
print(f'  New Price: ${new_price:,.2f} per ETH')

print(f'\nPrice moved: ${current_price:,.2f} -> ${new_price:,.2f}')
print('=' * 60)

# Compare: No fee vs With fee
print("\n" + "=" * 60)
print("COMPARISON: No Fee vs 0.3% Fee")
print("=" * 60)

amount_in = 1.0


no_fee = calculate_swap_output(eth_reserve, usdc_reserve, amount_in)
with_fee = calculate_swap_output_with_fee(eth_reserve, usdc_reserve, amount_in)

print(f'\nSwapping {amount_in} ETH:')
print(f'  No fee:    ${no_fee:,.2f} USDC')
print(f'  With .03%: ${with_fee:,.2f} USDC')
print(f'  Fee cost:  ${no_fee - with_fee:,.2f}')

print('\n' + '=' * 60)


def calculate_price_impact(reserve_in, reserve_out, amount_in):
    """
    Calculate price impact percentage from a swap

    Args:
        reserve_in: Reserve of token being sold
        reserve_out: Reserve of token being bought
        amount_in: Amount being swapped

    Returns:
        impact_percent: Price impact as a percentage    
    """

    #Price before swap
    price_before = reserve_out / reserve_in

    # Calculate new reserves after swap (with fee)
    amount_in_with_fee = amount_in * 0.997
    new_reserve_in = reserve_in + amount_in_with_fee
    new_reserve_out = (reserve_in * reserve_out / new_reserve_in)

    # Price after swap
    price_after = new_reserve_out / new_reserve_in

    # Caculate impact
    impact_percent = ((price_before - price_after) / price_before) * 100

    return impact_percent

# Test different trade sizes
print('\n' + '=' * 60)
print('PRICE IMPACT FOR DIFFERENT TRADE SIZES')
print('=' * 60)

trade_sizes = [0.1, 1.0, 5.0, 10.0, 50.0, 100.0]

print(f'\nPool: {eth_reserve} ETH / ${usdc_reserve:,.0f} USDC')
print(f'INitial Price: ${current_price:,.2f} per ETH\n')

for size in trade_sizes:
    output = calculate_swap_output_with_fee(eth_reserve, usdc_reserve, size)
    impact = calculate_price_impact(eth_reserve, usdc_reserve, size)

    effective_price = output / size

    print(f'{size:6.1f} ETH -> ${output:12,.2f} USDC')
    print(f'          Effective price: ${effective_price:,.2f} per ETH')
    print(f'          Price impact: {impact:.3f}%\n')

print('=' * 60) 

# Compare small pool vs large pool
print("\n" + "=" * 60)
print("SMALL POOL vs LARGE POOL COMPARISON")
print("=" * 60)

# Small pool (what we've been using)
small_eth = 100.0
small_usdc = 300000.0

# Large pool (realistic Uniswap V2 ETH/USDC size)
large_eth = 50000.0
large_usdc = 150000000.0  # $150M

trade = 10.0  # Swap 10 ETH in both

print(f"\nTrade size: {trade} ETH\n")

# Small pool
small_output = calculate_swap_output_with_fee(small_eth, small_usdc, trade)
small_impact = calculate_price_impact(small_eth, small_usdc, trade)

print(f"SMALL POOL ({small_eth} ETH / ${small_usdc:,.0f}):")
print(f"  Output: ${small_output:,.2f}")
print(f"  Price impact: {small_impact:.3f}%")

# Large pool
large_output = calculate_swap_output_with_fee(large_eth, large_usdc, trade)
large_impact = calculate_price_impact(large_eth, large_usdc, trade)

print(f"\nLARGE POOL ({large_eth:,.0f} ETH / ${large_usdc:,.0f}):")
print(f"  Output: ${large_output:,.2f}")
print(f"  Price impact: {large_impact:.3f}%")

print(f"\nDifference:")
print(f"  Large pool gives ${large_output - small_output:,.2f} MORE")
print(f"  Impact reduction: {small_impact - large_impact:.3f}%")

print("\n" + "=" * 60)