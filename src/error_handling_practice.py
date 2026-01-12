prices_checked = 0
errors_encountered = 0

uniswap_prices = {
    'Bitcoin': 50000,
    'Ethereum': 3000,
    'Solana': 100,
}

sushiswap_prcies = {
    'Bitcoin': 50100,
    'Ethereum': 2980,
    'Solana': 'unavailable',
}

print('Checking for arb opporutnities...\n')

for coin in uniswap_prices:
    try:
        uni_price = uniswap_prices[coin]
        sushi_price = sushiswap_prcies[coin]
        difference = sushi_price - uni_price
        print(f'{coin}: ${difference} difference')
    except (KeyError, TypeError):
        print(f'{coin} - Error occured')
        errors_encountered += 1
    finally:
        prices_checked += 1
        print(f'  [{prices_checked} coins checked so far]')

print(f'\nSummary:')
print(f'Total checked: {prices_checked}')
print(f'Errors: {errors_encountered}')
print(f'Successful: {prices_checked} - {errors_encountered}')