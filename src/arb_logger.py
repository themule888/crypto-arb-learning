import json
import csv

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(config)
        print(config['coins_to_check'])
        print(config['min_profit_threshold'])
except FileNotFoundError:
    print("Error: config.json not found!")

uniswap_prices = {
    'Bitcoin': 50000,
    'Ethereum': 3000,
    'Solana': 100
}

sushiswap_prices = {
    'Bitcoin': 50100,
    'Ethereum': 2980,
    'Solana': 100
}

opportunities = []

for coin in config['coins_to_check']:
    try:
        uni_price = uniswap_prices[coin]
        sushi_price = sushiswap_prices[coin]
        difference = uni_price - sushi_price
        print(f'The difference between {coin} is ${difference}')

        if abs(difference) > config['min_profit_threshold']:
            print(f'-> {coin} MEETS YOUR THRESHOLD')

            opportunity = {
                'coin': coin,
                'uniswap_price': uni_price,
                'sushiswap_price': sushi_price,
                'difference' : difference
            }
            opportunities.append(opportunity)
 
    except KeyError:
        print(f'Error: {coin} data missing')

with open('opportunities.csv', 'w') as arb_log:
    log_writer = csv.DictWriter(arb_log, fieldnames = ['coin', 'uniswap_price', 'sushiswap_price', 'difference'])
    log_writer.writeheader()

    for opportunity in opportunities:
        log_writer.writerow(opportunity)
 
