import requests

url = 'https://api.coingecko.com/api/v3/simple/price'

params = {
    'ids': 'bitcoin',
    'vs_currencies': 'usd'
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
    price = data['bitcoin']['usd']
    print(f'Bitcoin price: ${price}')
