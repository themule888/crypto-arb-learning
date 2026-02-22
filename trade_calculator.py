# Trade Size Optimizer
# Given a pool and spread, find optimal trade size

def calculate_profit(trade_size_usd, spread_pct, pool_tvl, gas_cost_usd=2.0):
    """
    Calculate net profit for a given trade size

    trade_size_usd: how much USDC you're trading
    spreaD_pct:     price dfference between DEXs (e.g 0.196)
    pool_tvl:       total value locked in the samller pool
    gas_cost_usd:   gas cost in dollars (default $2 for L2)
    """

    # Gross profit before costs
    gross_profit = trade_size_usd * (spread_pct / 100)

    # Price impact (larger trade = more slippage)
    price_impact_pct = (trade_size_usd / pool_tvl) * 100
    impact_cost = trade_size_usd * (price_impact_pct / 100)

    # Net profit
    net_profit = gross_profit - impact_cost - gas_cost_usd

    return {
        'trade_size': trade_size_usd,
        'gross_profit': gross_profit,
        'impact_cost': impact_cost,
        'gas_cost': gas_cost_usd,
        'net_profit': net_profit
    }

# Test with today's real data from our scanner
spread_pct = 0.196
pool_tvl = 21317 # ShibaSwap TVL (smallest pool = most impact)

print(f'Spread: {spread_pct}%  |  Pool TVL: ${pool_tvl:,}')
print(f'\n{"Trade Size":>12} {"Gross":>10} {"Impact":>10} {"Gas":>8} {"NET":>10}')
print('-' * 55)

for trade_size in [100, 500, 1000, 2000, 5000, 10000]:
    r = calculate_profit(trade_size, spread_pct, pool_tvl)
    print(f'${r["trade_size"]:>11,.0f} ${r["gross_profit"]:>9,.2f} ${r["impact_cost"]:>9,.2f} ${r["gas_cost"]:>7,.2f} ${r["net_profit"]:>9,.2f}')

# Same spread, but Uniswap's pool (much deeper)
print(f'\n--- Same spread, Uniswap pool ($17M TVL) ---')
pool_tvl = 17859169

print(f'\n{"Trade Size":>12} {"Gross":>10} {"Impact":>10} {"Gas":>8} {"NET":>10}')
print('-' * 55)

for trade_size in [1000, 5000, 10000, 25000, 50000, 100000]:
    r = calculate_profit(trade_size, spread_pct, pool_tvl)
    print(f'${r["trade_size"]:>11,.0f} ${r["gross_profit"]:>9,.2f} ${r["impact_cost"]:>9,.2f} ${r["gas_cost"]:>7,.2f} ${r["net_profit"]:>9,.2f}')

def find_optimal_size(spread_pct, pool_tvl, gas_cost_usd=2.0):
    """Find the trade size that maximizes net profit"""
    best = {'net_profit': - 999999, 'trade_size': 0}

    for size in range(100, 200000, 100):
        r = calculate_profit(size, spread_pct, pool_tvl, gas_cost_usd)
        if r['net_profit'] > best ['net_profit']:
            best = r
    
    return best

result = find_optimal_size(spread_pct, 17859169)
print(f'\n🎯 Optimal trade size: ${result["trade_size"]:,.0f}')
print(f'   Expected profit: ${result["net_profit"]:,.2f}')