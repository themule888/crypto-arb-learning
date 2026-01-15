import requests
import time
import csv
from datetime import datetime

# Alert threshold setting
ALERT_THRESHOLD = 0.5 # Alert if prcie moves more than 0.5%

gecko_url = 'https://api.coingecko.com/api/v3/simple/price'

params = {
    'ids': 'bitcoin',
    'vs_currencies': 'usd'
}

previous_price = None

while True:
    gecko_success = False

    # Fetch Bitcoin price from Gecko
    try:
        response_gecko = requests.get(gecko_url, params=params)
    
        if response_gecko.status_code == 200:
            data_gecko = response_gecko.json()
        
            if 'bitcoin' in data_gecko:
                gecko_price = data_gecko['bitcoin']['usd']
                gecko_success = True
            else:
                print('Error: Bitcoin not found in CoinGecko response')
        else:
            print(f'CoinGecko API Error: Status code {response_gecko.status_code}')

    except requests.exceptions.RequestException as e:
        print(f'Error fetching CoinGecko prices: {e}')

    if gecko_success:
        print(f'CoinGecko: ${gecko_price:,.2f}')
        # Check if we have previous price to compare
        if previous_price is not None:
            change_dollar = gecko_price - previous_price
            change_percent = ((gecko_price - previous_price)/ previous_price) * 100
            print(f'Change: ${change_dollar:,.2f} ({change_percent:+.2f}%)')

            # Alert on large movements
            if abs(change_percent) >= ALERT_THRESHOLD:
                print(f'🚨 ALERT: Large price movement! {change_percent:+.2f}%')
        else:
            print('(First fetch - no previous price)')

        # Log to CSV
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open ('bitcoin_price.csv', 'a', newline='') as file:
            writer = csv.writer(file)

            # Writer header if ffile is new
            if previous_price is None:
                writer.writerow(['Timestamp', 'Price', 'Change_Dollar', 'Change_Percent'])

            # Write Data
            if previous_price is not None:
                writer.writerow([timestamp, gecko_price, change_dollar, f'{change_percent:.2f}'])
            else:
                writer.writerow([timestamp, gecko_price, 'N/A', 'N/A'])

        # Save Current price for next comparison
        previous_price = gecko_price
    else:
        print('Failed to fetch price this time')

    print('---')
    time.sleep(30)