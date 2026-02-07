import requests
import argparse

def get_coingecko_price(coin):
    """Fetch price from CoinGecko"""
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': coin, 'vs_currencies': 'usd'}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if coin in data:
                return data[coin]['usd']
    except:
        pass
    return None

def get_coincap_price(coin):
    """Fetch price from CoinCap"""
    url = f'https://api.coincap.io/v2/assets/{coin}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'priceUsd' in data['data']:
                return float(data['data']['priceUsd'])
    except:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='Compare crypto prices across exchanges')
    parser.add_argument('--coin', type=str, default='bitcoin', help='Coin to track (default: bitcoin)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Alert threshold percent (default: 0.5)')
    
    args = parser.parse_args()
    
    print(f'Fetching {args.coin} prices from multiple exchanges...\n')
    
    # Fetch from both exchanges
    gecko_price = get_coingecko_price(args.coin)
    coincap_price = get_coincap_price(args.coin)
    
    # Display prices
    if gecko_price:
        print(f'CoinGecko: ${gecko_price:,.2f}')
    else:
        print('CoinGecko: Failed to fetch')
    
    if coincap_price:
        print(f'CoinCap:   ${coincap_price:,.2f}')
    else:
        print('CoinCap: Failed to fetch')
    
    # Compare prices if both succeeded
    if gecko_price and coincap_price:
        difference = abs(gecko_price - coincap_price)
        percent_diff = (difference / gecko_price) * 100
        
        print(f'\nPrice difference: ${difference:,.2f} ({percent_diff:.2f}%)')
        
        if percent_diff >= args.threshold:
            print(f'🚨 ALERT: Price difference exceeds {args.threshold}% threshold!')

if __name__ == '__main__':
    main()