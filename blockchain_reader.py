from web3 import Web3

# Infura API key
INFURA_API_KEY = 'af63bf5e933b419b9f96b021ce430232'

# Connect to Ethereum mainnet via Infura
infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check if connected
if web3.is_connected():
    print('✅ Connected to Ethereum mainnet!')
else:
    print('❌ Connection failed')
    exit()

# Get latest block number
latest_block = web3.eth.block_number
print(f'\n📦 Latest block number: {latest_block}')

# Get full block data
block = web3.eth.get_block(latest_block)
print(f'📊 Block Details:')
print(f'  Timestamp: {block["timestamp"]}')
print(f'  Transactions: {len(block["transactions"])}')
print(f'  Gas Used: {block["gasUsed"]:,}')
print(f'  Miner: {block["miner"]}')

# Vitas Ethereum address
vitalik_address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'

# Get balance (in Wei - smallest unit of ETH)
balance_wei = web3.eth.get_balance(vitalik_address)

#Convert Wei to ETH (1 ETH = 10^18 Wei)
balance_eth = web3.from_wei(balance_wei, 'ether')

print(f'\n 💰 Vita\'s Balance:')
print(f'  Address: {vitalik_address}')
print(f'  Balance: {balance_eth} ETH')

# Your MetaMask Address
my_address = '0x0F92e810478f2225841137B34D8C63c1950eD4f6'

# Check your balance on SEPOLIA testnet
sepolia_url = f'https://sepolia.infura.io/v3/{INFURA_API_KEY}'
web3_sepolia = Web3(Web3.HTTPProvider(sepolia_url))

my_balance_wei = web3_sepolia.eth.get_balance(my_address)
my_balance_eth = web3_sepolia.from_wei(my_balance_wei, 'ether')

print(f'\n💰 My Sepolia Balance:')
print(f'  Address: {my_address}')
print(f'  Balance: {my_balance_eth} SepoliaETH')

# Example transaction hash (a real Ethereum transaction)
tx_hash = '0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060'

print(f'\n🔍 Transaction Details:')
print(f'  Hash: {tx_hash}')

# Get transaction data
tx = web3.eth.get_transaction(tx_hash)

print(f'  From: {tx["from"]}')
print(f'  To: {tx["to"]}')
print(f'  Value: {web3.from_wei(tx["value"], "ether")} ETH')
print(f'  Gas Price: {web3.from_wei(tx["gasPrice"], "gwei")} Gwei')
print(f'  Block: {tx["blockNumber"]}')