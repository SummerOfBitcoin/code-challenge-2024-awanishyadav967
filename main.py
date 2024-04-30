import json
import hashlib
import os

# Define the difficulty target
DIFFICULTY_TARGET = int("0000ffff00000000000000000000000000000000000000000000000000000000", 16)

# Helper functions
def validate_transaction(transaction):
    # Placeholder function for transaction validation
    # You can implement your own transaction validation logic here
    # For simplicity, let's assume all transactions are valid if they have required fields

    # Check if the transaction has all required fields
    required_fields = ["version", "locktime", "vin", "vout"]
    for field in required_fields:
        if field not in transaction:
            return False

    # Check if the version is valid
    if not isinstance(transaction["version"], int) or transaction["version"] != 1:
        return False

    # Check if the locktime is valid
    if not isinstance(transaction["locktime"], int) or transaction["locktime"] < 0:
        return False

    # Check if the input list is non-empty
    if not isinstance(transaction["vin"], list) or len(transaction["vin"]) == 0:
        return False

    # Check if the output list is non-empty
    if not isinstance(transaction["vout"], list) or len(transaction["vout"]) == 0:
        return False

    # Additional validation rules can be added here

    # If all checks pass, consider the transaction as valid
    return True


def hash_transaction(transaction):
    # Hash the transaction using SHA-256
    transaction_string = json.dumps(transaction, sort_keys=True).encode()
    return hashlib.sha256(transaction_string).hexdigest()

def mine_block(transactions):
    # Construct the block header (placeholder for now)
    block_header = "Block Header Placeholder"

    # Serialize the coinbase transaction
    coinbase_transaction = {"txid": "Coinbase", "inputs": [], "outputs": [{"value": 50, "scriptPubKey": ""}]}
    coinbase_txid = hash_transaction(coinbase_transaction)
    serialized_coinbase = json.dumps(coinbase_transaction).encode().hex()

    # Start mining
    valid_transactions = [coinbase_txid]
    for tx in transactions:
        if validate_transaction(tx):
            txid = hash_transaction(tx)
            valid_transactions.append(txid)

    # Write the output to output.txt
    with open("output.txt", "w") as f:
        f.write(block_header + "\n")
        f.write(serialized_coinbase + "\n")
        for txid in valid_transactions:
            f.write(txid + "\n")


def main():
    # Load transactions from the mempool folder
    mempool_dir = "mempool"
    transactions = []
    for filename in os.listdir(mempool_dir):
        with open(os.path.join(mempool_dir, filename), "r") as f:
            transaction = json.load(f)
            transactions.append(transaction)

    # Mine the block
    mine_block(transactions)

if __name__ == "__main__":
    main()
