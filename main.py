import json
import hashlib
import os

# Constants
MEMPOOL_DIR = "mempool"
OUTPUT_FILE = "output.txt"
BLOCK_REWARD = 50 * 10**8  # 50 BTC in satoshis

# Helper functions
def validate_transaction(tx):
    """Validate a transaction based on specific rules"""
    # Check if the transaction has all required fields
    required_fields = ["version", "locktime", "vin", "vout"]
    for field in required_fields:
        if field not in tx:
            return False

    # Implement additional validation rules as needed

    return True

def hash_transaction(tx):
    """Hash a transaction using SHA-256"""
    tx_string = json.dumps(tx, sort_keys=True).encode()
    return hashlib.sha256(tx_string).hexdigest()

def mine_block(transactions):
    """Mine a new block with the given transactions"""
    # Serialize the coinbase transaction
    coinbase_tx = {
        "txid": "coinbase_tx",
        "vout": [{"value": BLOCK_REWARD, "scriptPubKey": ""}]
    }
    coinbase_txid = hash_transaction(coinbase_tx)
    serialized_coinbase = json.dumps(coinbase_tx).encode().hex()

    # Start mining
    valid_transactions = [coinbase_txid]
    for tx in transactions:
        if validate_transaction(tx):
            txid = hash_transaction(tx)
            valid_transactions.append(txid)

    # Write the block to the output file
    with open(OUTPUT_FILE, "w") as f:
        # Write serialized coinbase transaction
        f.write(serialized_coinbase + "\n")
        # Write transaction IDs
        for txid in valid_transactions:
            f.write(txid + "\n")

def main():
    """Main function to load transactions and mine the block"""
    # Load transactions from the mempool directory
    transactions = []
    for filename in os.listdir(MEMPOOL_DIR):
        filepath = os.path.join(MEMPOOL_DIR, filename)
        with open(filepath, "r") as file:
            tx = json.load(file)
            transactions.append(tx)

    # Mine a new block
    mine_block(transactions)

if __name__ == "__main__":
    main()
