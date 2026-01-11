# My crypto holdings
holdings = {
    'Bitcoin': 0.5,
    'Ethereum': 2.0,
    'Solana': 10.0,
}

# Current prices (hardcoded for now)
prices = {
    'Bitcoin': 50000,
    'Ethereum': 3000,
    'Solana': 100
}
# Calculate total value
total_value = 0

for coin in holdings:
    amount = holdings[coin]
    price = prices[coin]
    value = amount * price
    total_value = total_value + value
    print(f'{coin}: {amount} coins x ${price} = ${value}')

print(f'\nTotal portfolio Value: {total_value}')
