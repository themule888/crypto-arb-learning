from web3 import Web3

# Your Infura API Key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check connection
if web3.is_connected():
    print('✅ Connected to Ethereum mainnet')
else:
    print('❌ Connection failed')
    exit()

# USDC contract address
usdc_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

# Event signature for Transfer event
# Transfer(address indexed from, address indexed to, uint256 value)
transfer_event_signature = web3.keccak(text='Transfer(address,address,uint256)').hex()

print(f'\n📡 Transfer Event Signature: {transfer_event_signature}')

# Get Latest Block Number
latest_block = web3.eth.block_number
print(f'\n📦 Latest block:: {latest_block}')

# Define Block Range
from_block = latest_block - 10
to_block = latest_block
print(f'🔍 Scanning blocks {from_block} to {to_block}...\n')

# Event Filter
event_filter = web3.eth.filter({
    'fromBlock': from_block,
    'toBlock': to_block,
    'address': usdc_address,
    'topics': ['0x' + transfer_event_signature]
})

#Fetch Events
events = event_filter.get_all_entries()

print(f'Found {len(events)} Transfer events in last 10 blocks')
print('=' * 60)

# Minimal ERC-20 ABI for decoding Transfer events
erc20_abi = [
    {
        'anonymous': False,
        'inputs': [
            {'indexed': True, 'name': 'from', 'type': 'address'},
            {'indexed': True, 'name': 'to', 'type': 'address'},
            {'indexed': False, 'name': 'value', 'type': 'uint256'}
        ],
        'name': 'Transfer',
        'type': 'event'
    }
]

# Create contract instance for decoding
usdc_contract = web3.eth.contract(address=usdc_address, abi=erc20_abi)

print('\n🔍 DECODED TRANSFER EVENTS:')
print('=' * 80)

# Whale Filter
print('\n🐳 WHALE TRANSFERS (>$100,000):')
print('=' * 80)

whale_count = 0

for i, event in enumerate(events): # Loop through ALL events now
    # Decode the event using the contract
    decoded = usdc_contract.events.Transfer().process_log(event)

    # Extract data
    from_address = decoded['args']['from']
    to_address = decoded['args']['to']
    value_raw = decoded['args']['value']

    # Convert value (USDC has 6 decimals)
    value_usdc = value_raw / 10**6

    #Filter: Only show transfers > $100,000
    if value_usdc > 100000:
        whale_count += 1

        # Get Block and transaction info
        block_number = decoded['blockNumber']
        tx_hash = decoded['transactionHash'].hex()

        print(f'\n🐋 Whale Transfer #{whale_count}:')
        print(f'  From:    {from_address}')
        print(f'  To:      {to_address}')
        print(f'  Amount:  ${value_usdc:,.2f} USDC')
        print(f'  Block:   {block_number}')
        print(f'  Tx:      {tx_hash[:20]}...')

print(f'\n📊 Summary:')
print(f'  Total transfers: {len(events)}')
print(f'  Whale transfers (>$100K): {whale_count}')