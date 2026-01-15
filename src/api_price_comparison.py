import requests

gecko_url = 'https://api.coingecko.com/api/v3/simple/price'
cap_url = 'https://api.coincap.io/v2/assets/bitcoin'

params = {
    'ids': 'bitcoin',
    'vs_currencies': 'usd'
}

gecko_success = False
cap_success = False

# Fetch from CoinGecko
try:
    response_gecko = requests.get(gecko_url, params=params)
    
    if response_gecko.status_code == 200:
        data_gecko = response_gecko.json()
        print('CoinGecko Response:', data_gecko)
        
        if 'bitcoin' in data_gecko:
            gecko_price = data_gecko['bitcoin']['usd']
            gecko_success = True
        else:
            print('Error: Bitcoin not found in CoinGecko response')
    else:
        print(f'CoinGecko API Error: Status code {response_gecko.status_code}')

except requests.exceptions.RequestException as e:
    print(f'Error fetching CoinGecko prices: {e}')

# Fetch from CoinCap
try:
    response_cap = requests.get(cap_url)
    
    if response_cap.status_code == 200:
        data_cap = response_cap.json()
        print('CoinCap Response:', data_cap)
        
        if 'data' in data_cap:
            cap_price = float(data_cap['data']['priceUsd'])
            cap_success = True
        else:
            print('Error: Data not found in CoinCap response')
    else:
        print(f'CoinCap API Error: Status code {response_cap.status_code}')

except requests.exceptions.RequestException as e:
    print(f'Error fetching CoinCap prices: {e}')

# Compare prices only if both succeeded
if gecko_success and cap_success:
    difference = abs(gecko_price - cap_price)
    
    print(f'\n--- Price Comparison ---')
    print(f'CoinGecko: ${gecko_price:,.2f}')
    print(f'CoinCap:   ${cap_price:,.2f}')
    print(f'Difference: ${difference:,.2f}')
    
    if gecko_price > cap_price:
        print(f'💡 CoinCap is cheaper by ${difference:,.2f}')
    elif cap_price > gecko_price:
        print(f'💡 CoinGecko is cheaper by ${difference:,.2f}')
    else:
        print('✅ Prices are identical!')
else:
    print('\n❌ Could not compare prices - one or both API calls failed')

    