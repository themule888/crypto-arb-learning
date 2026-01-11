import csv

# Prices on Uniswap 
uniswap_prices = {
    'Bitcoin': 50000,
    'Ethereum': 3000,
    'Solana': 100
}

# Prices on Sushiswap
sushiswap_prices = {
    'Bitcoin': 50100,
    'Ethereum': 2980,
    'Solana': 100
}

opportunities = []

print('Price comparison started!')

for coin in uniswap_prices:
    uni_price = uniswap_prices[coin]
    sushi_price = sushiswap_prices[coin]
    print(f'{coin}: Uniswap = ${uni_price}, Sushiswap = ${sushi_price}')

    difference = sushi_price - uni_price
    print(f'Difference: ${difference}')

    profit_for_10 = difference * 10
    print(f'Profit if you trade 10 coins: ${profit_for_10}')

    opportunity = {
        'coin': coin,
        'uniswap_price': uni_price,
        'sushiswap_price': sushi_price,
        'difference' : difference,
        'profit_10_coins': profit_for_10
    }
    opportunities.append(opportunity)

    if difference > 0:
        print(f'-> Uniswap is cheaper! Buy there, sell on Sushiswap')
    elif difference < 0:
        print(f'Sushiswap is cheaper! Buy there, sell on Uniswap')
    else:
        print(f'-> Same price on both exchanges')
    
    print()

with open('arb_log.csv', 'w') as arb_log:
    log_writer = csv.DictWriter(arb_log, fieldnames = ['coin', 'uniswap_price', 'sushiswap_price', 'difference', 'profit_10_coins'])
    log_writer.writeheader()

    for opportunity in opportunities:
        log_writer.writerow(opportunity)


