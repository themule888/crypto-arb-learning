# Final Exercise - Arbitrage Opportunity Logger

# Exchange 1 prices
binance_prices = {
    'Bitcoin': 50000,
    'Ethereum': 3000,
    'Solana': 100,
    'Cardano': 0.50,
    'Polygon': 0.80
}

# Exchange 2 prices (has issues)
kraken_prices = {
    'Bitcoin': 50150,
    'Ethereum': 'N/A',      # Bad data - string instead of number
    'Solana': 99.50,
    # Cardano is missing
    'Polygon': 0.00         # Division by zero issue later
}

# Tracking variables
total_checks = 0
errors_count = 0
opportunities = []

print('=== Starting Arbitrage Scanner ===\n')

for coin in binance_prices:
    try:
        binance_price = binance_prices[coin]
        kraken_price = kraken_prices[coin]
        percent_diff = ((kraken_price - binance_price) / binance_price) * 100
        profit_potential = 100 / kraken_price
        print(f'{coin}: Binance = ${binance_price}, Kraken = ${kraken_price}, Diff = {percent_diff}%')
    except KeyError:
        print(f'{coin} is missing from Kraken')
        errors_count += 1
    except TypeError:
        print(f'{coin} has bad data from Kraken')
        errors_count += 1
    except ZeroDivisionError:
        print(f'{coin} has zero price on Kraken - invalid data')
        errors_count += 1
    else:
        if abs(percent_diff) > 1.0:
            print('-> OPPORTUNITY FOUND!')
            opportunities.append({'coin': coin, 'percent': percent_diff})
    finally:
        total_checks += 1

print(f'total checks: {total_checks}')
print(f'Errors Counted: {errors_count}')
print(f'Successful: {total_checks - errors_count}')
print(f'Oppotunities found: {len(opportunities)}')

if len(opportunities) > 0:
    print()
    print('Opportunity Details:')
    for opp in opportunities:
        print(f'{opp['coin']}: {opp['percent']} difference ')

