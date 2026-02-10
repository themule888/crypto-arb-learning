from web3 import Web3

# Your Infura API Key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check Conecction
if web3.is_connected():
    print('✅ Connected to Ethereum mainnet!')
else:
    print('❌ Connection failed')
    exit()

# Uniswap V2 Pair contract ABI (minimal - just what we need)
uniswap_pair_abi = [
    {
        'constant': True,
        'inputs': [],
        'name': 'getReserves',
        'outputs': [
            {'name': 'reserve0', 'type': 'uint112'},
            {'name': 'reserve1', 'type': 'uint112'},
            {'name': 'blockTimestampLast', 'type': 'uint32'}
        ],
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'token0',
        'outputs': [{'name': '', 'type': 'address'}],
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'token1',
        'outputs': [{'name': '', 'type': 'address'}],
        'type': 'function'
    }
]

# ETH/USDC Uniswap V2 pair address
eth_usdc_pair = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'

# Create pair contract instance
pair_contract = web3.eth.contract(address=eth_usdc_pair, abi=uniswap_pair_abi)

# Check whick token is which
token0_address = pair_contract.functions.token0().call()
token1_address = pair_contract.functions.token1().call()

print(f'\n🔍 Pool Token Addresses:')
print(f'  Token0: {token0_address}')
print(f'  Token1: {token1_address}')

# Get reserves
reserves = pair_contract.functions.getReserves().call()

print(f'\n📊 ETH/USDC Uniswap Pool:')
print(f'  Reserve0 (WETH): {reserves[0]:,}')
print(f'  Reserve1 (USDC): {reserves[1]:,}')

# Convert to human-reable amounts
# Token0 is USDC, Token1 is WETH 
usdc_reserves = reserves[0] / 10**6   # Token0 = USDC (6 decimals)
weth_reserves = reserves[1] / 10**18  # Token1 = WETH (18 decimals)

print(f'\n💰 Human-Reable Reserves:')
print(f'  WETH: {weth_reserves:,.2f} ETH')
print(f'  USDC: ${usdc_reserves:,.2f}')

# Caclulate ETH price from reserves
eth_price = usdc_reserves / weth_reserves

print(f'\n📈 ETH Price (from reserves):')
print(f'  ${eth_price:,.2f} per ETH')

# Compare to CoinGecko API
print('\n🔁 Comparing to CoinDeck API...')

import requests

gecko_url = 'https://api.coingecko.com/api/v3/simple/price'
params = {'ids': 'ethereum', 'vs_currencies': 'usd'}

try:
    response = requests.get(gecko_url, params=params)
    if response.status_code == 200:
        data = response.json()
        gecko_price = data['ethereum']['usd']

        print(f'\n💹 Price Comparison:')
        print(f'  Uniswap (DEX):    ${eth_price:,.2f}')
        print(f'  CoinGecko (avg):  ${gecko_price:,.2f}')

        difference  = abs(eth_price - gecko_price)
        percent_diff = (difference / gecko_price) * 100

        print(f'  Difference: ${difference:,.2f} ({percent_diff:.2f}%)')

except Exception as e:
    print(f'  Error: {e}')


# SushiSwap ETH/USDC pair address
sushiswap_eth_usdc = '0x397FF1542f962076d0BFE58eA045FfA2d347ACa0'

print('\n🍣 Reading SushiSwap Pool...')

# Create SushiSwap contract
sushi_contract = web3.eth.contract(address=sushiswap_eth_usdc, abi=uniswap_pair_abi)

# Get SushiSwap reserve
sushi_reserves = sushi_contract.functions.getReserves().call()

# Check token order (might be different than Uniswap)
sushi_token0 = sushi_contract.functions.token0().call()

# Convert reserves (checking which is which)
if sushi_token0.lower() == '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'.lower():
    # Token0 is USDC
    sushi_usdc = sushi_reserves[0] / 10**6
    sushi_weth = sushi_reserves[1] / 10**18
else:
    # Token0 is WETH
    sushi_weth = sushi_reserves[0] / 10**18
    sushi_usdc = sushi_reserves[1] / 10**6

# Calculate SushiSwap Price
sushi_price = sushi_usdc / sushi_weth

print(f'\n💰 SushiSwap Reserves')
print(f'  WETH: {sushi_weth:,.2f}')
print(f'  USDC: ${sushi_usdc:,.2f}')
print(f'  Price: ${sushi_price:,.2f} per ETH')

# ARBITRAGE DETECTION
print(f'\n ARBITRAGE ANALYSIS:')
print(f'  Uniswap:  ${eth_price:,.2f}')
print(f'  SuhsiSwap: ${sushi_price:,.2f}')

arb_diff = abs(eth_price - sushi_price)
arb_percent = (arb_diff / eth_price) * 100

print(f'  Spead: ${arb_diff:,.2f} ({arb_percent:.3f}%)')

if arb_diff > 5:
    if eth_price < sushi_price:
        print(f'  ⚡️ OPPORTUNITY: Buy on Uniswap (${eth_price:,.2f}), Sell on SushiSwap (${sushi_price:,.2f})')
    else:
        print(f'  ⚡️OPPORTUNITY: Buy on SushiSwap (${sushi_price:,.2f}), Sell on Uniswap (${eth_price:,.2f})')
else:
    print(f'  ✅ No siginicant arbitrage (spread < $5)')