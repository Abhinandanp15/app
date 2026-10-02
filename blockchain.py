from web3 import Web3

RPC_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

contract_address = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "investor", "type": "address"},
            {"internalType": "uint256", "name": "propertyId", "type": "uint256"},
            {"internalType": "uint256", "name": "units", "type": "uint256"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=abi)

PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

def mint_tokens(wallet, property_id, units):
    account = w3.eth.account.from_key(PRIVATE_KEY)

    txn = contract.functions.mint(
        Web3.to_checksum_address(wallet),
        property_id,
        units
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 3000000,
        "gasPrice": w3.to_wei("1", "gwei"),
        "chainId": 31337
    })

    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return tx_hash.hex()