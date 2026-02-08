from web3 import Web3

# Your infura API key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check connection
if web3.is_connected():
    print('✅ Connected to Ethereum mainnet!')
else:
    print('❌ Connection failed')
    exit()

# USDC token contract address on Ethereum
usdc_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

# Minimal ERC-20 ABI (just the functions as we need)
erc20_abi = [
    {
    'constant': True,
    'inputs': [{'name': '_owner', 'type': 'address'}],
    'name': 'balanceOf',
    'outputs': [{'name': 'balance', 'type': 'uint256'}],
    'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'decimals',
        'outputs': [{'name': '', 'type': 'uint8'}],
        'type': 'function'
    },
    {
        'constant': True,
        'inputs': [],
        'name': 'symbol',
        'outputs': [{'name': '', 'type': 'string'}],
        'type': 'function'
    }
]

# Create contract instance
usdc_contract = web3.eth.contract(address=usdc_address, abi=erc20_abi)

# Get Token Symbol
token_symbol = usdc_contract.functions.symbol().call()
token_decimals = usdc_contract.functions.decimals().call()

print(f'\n💎 Token Info:')
print(f'  Symbol: {token_symbol}')
print(f'  Decimals: {token_decimals}')

# Check USDC balance for Vitalik's address
vitalik_address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'

# Get raw balance
raw_balance = usdc_contract.functions.balanceOf(vitalik_address).call()

# convert to human-reable (divid by 10^decimals)
usdc_balance = raw_balance / (10 ** token_decimals)

print(f'\n💰 USDC Balance:')
print(f'  Address: {vitalik_address}')
print(f'  Raw balance: {raw_balance:,}')
print(f'  USDC balance: {usdc_balance:,.2f} USDC')

# Function to check ERC-20 token Balance
def get_token_balance(token_address, wallet_address):
    """Get token balance for any ERC-20 token"""

    # Create contract instance
    contract = web3.eth.contract(address=token_address, abi=erc20_abi)

    # Get token info
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()

    # Get Balance
    raw_balance = contract.functions.balanceOf(wallet_address).call()
    balance = raw_balance / 10 ** decimals

    return {
        'symbol': symbol,
        'balance': balance,
        'raw_balance': raw_balance
    }

# Test with multiple tokens
print(f'🏦 Multi-Token Balance Check')

# Token addresses
tokens = {
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
}

# Check all tokens for Vitalik
for token_name, token_address in tokens.items():
    result = get_token_balance(token_address, vitalik_address)
    print(f'  {result["symbol"]}: {result["balance"]:,.2f}')

# Check your tokens on mainnet
your_address = '0x0F92e810478f2225841137B34D8C63c1950eD4f6'

print(f'\n💳 Your Token Balances:')
for token_name, token_address in tokens.items():
    result = get_token_balance(token_address, your_address)
    print(f'  {result["symbol"]}: {result["balance"]:,.6f}')
