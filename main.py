import json
import hashlib
import os
import time


# Constants
DIFFICULTY_TARGET = "0000ffff00000000000000000000000000000000000000000000000000000000"
MEMPOOL_DIR = "mempool"
OUTPUT_FILE = "output.txt"
BLOCK_REWARD = 50 * 10**8  # 50 BTC in satoshis

def calculate_merkle_root(transactions):
    # Calculate merkle root hash
    # You can implement a merkle tree algorithm here
    # For simplicity, let's just concatenate and hash all transaction IDs
    txids_bytes = [hash_transaction(tx).encode() for tx in transactions]  # Convert to bytes
    merkle_root = hashlib.sha256(b"".join(sorted(txids_bytes))).hexdigest()
    return merkle_root


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
    # Calculate merkle root
    merkle_root = calculate_merkle_root(transactions)

    # Create a valid block header
    block_header = {
        "version": 1,
        "prev_block_hash": "0000000000000000000000000000000000000000000000000000000000000000",  # Placeholder
        "merkle_root_hash": merkle_root,
        "timestamp": int(time.time()),
        "nonce": 0
    }

    # Mine the block by finding a suitable nonce
    while True:
        block_header["nonce"] += 1
        block_hash = hashlib.sha256(json.dumps(block_header, sort_keys=True).encode()).hexdigest()
        if block_hash < DIFFICULTY_TARGET:
            break

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
        f.write(json.dumps(block_header) + "\n")
        f.write(serialized_coinbase + "\n")
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
