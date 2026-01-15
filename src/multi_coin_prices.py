import requests

url = 'https://api.coingecko.com/api/v3/simple/price'

params = {
    'ids': 'bitcoin,ethereum,solana',
    'vs_currencies': 'usd'
}

try:
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(data)
        if 'bitcoin' in data and 'ethereum' in data and 'solana' in data:
            btc_price = data['bitcoin']['usd']
            eth_price = data['ethereum']['usd']
            sol_price = data['solana']['usd']
            print(f'Bitcoin price: ${btc_price}')
            print(f'Ethereum price: ${eth_price}')
            print(f'Solana price: ${sol_price}')
        else:
            print('Error: One or more coins not found in API response')
    else:
        print(f'API Error: Status code {response.status_code}')

except requests.exceptions.RequestException as e:
    print(f'Error fetching prices: {e}')

