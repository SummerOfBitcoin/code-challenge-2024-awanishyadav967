import os
import json
import hashlib
import time
from typing import List, Tuple, Dict

# Define the difficulty target
DIFFICULTY_TARGET = "0000ffff00000000000000000000000000000000000000000000000000000000"
BLOCK_REWARD = 50  # Assuming a block reward of 50 bitcoins

# Helper functions
def double_sha256(data: bytes) -> bytes:
    """
    Compute the double SHA-256 hash of the given data.
    """
    hash1 = hashlib.sha256(data).digest()
    hash2 = hashlib.sha256(hash1).digest()
    return hash2

def validate_transaction(transaction: Dict, mempool: Dict[str, Tuple[int, Dict]]) -> bool:
    """
    Validate a Bitcoin transaction using the mempool.
    """
    # Check if the transaction has at least one input
    inputs = transaction.get("vin", [])
    if not inputs:
        return False

    # Check if the transaction has at least one output
    outputs = transaction.get("vout", [])
    if not outputs:
        return False

    # Check if the sum of input values is greater than or equal to the sum of output values
    input_value = sum(validate_input(input_data, transaction, mempool) for input_data in inputs)
    output_value = sum(output.get("value", 0) for output in outputs)
    if input_value < output_value:
        return False

    # Check if the transaction version is valid
    if transaction.get("version", 0) != 1:
        return False

    # Check if the locktime is valid
    if transaction.get("locktime", 0) < 0:
        return False

    return True

def validate_input(input_data: Dict, transaction: Dict, mempool: Dict[str, Tuple[int, Dict]]) -> int:
    """
    Validate an input and return its value using the mempool.
    """
    # Check if the input has a valid previous output reference
    prev_out = input_data.get("prevout")
    if not prev_out or not isinstance(prev_out, dict):
        return 0

    prev_tx_id = prev_out.get("txid")
    prev_tx_index = prev_out.get("voutIndex")

    if prev_tx_id is None or prev_tx_index is None:
        return 0

    prev_tx_info = mempool.get(prev_tx_id)
    if prev_tx_info is None:
        return 0

    prev_tx_value, prev_tx = prev_tx_info
    prev_output = prev_tx.get("vout", [])

    if prev_tx_index >= len(prev_output):
        return 0

    prev_output_value = prev_output[prev_tx_index].get("value", 0)

    # Verify the signature script against the public key script
    # (Omitted for simplicity)

    return prev_output_value

def calculate_merkle_root(transactions: List[dict]) -> str:
    """
    Calculate the Merkle root of the given transactions.
    """
    transaction_hashes = [double_sha256(json.dumps(tx).encode()) for tx in transactions]

    while len(transaction_hashes) > 1:
        if len(transaction_hashes) % 2 != 0:
            transaction_hashes.append(transaction_hashes[-1])

        new_hashes = []
        for i in range(0, len(transaction_hashes), 2):
            combined_hash = double_sha256(transaction_hashes[i] + transaction_hashes[i + 1])
            new_hashes.append(combined_hash)

        transaction_hashes = new_hashes

    return transaction_hashes[0].hex()

def construct_block_header(prev_block_hash: str, merkle_root: str, timestamp: int, nonce: int) -> bytes:
    """
    Construct the block header according to the Bitcoin protocol.
    """
    block_header = (
        bytes.fromhex(prev_block_hash)
        + bytes.fromhex(merkle_root)
        + timestamp.to_bytes(4, byteorder="little")
        + nonce.to_bytes(4, byteorder="little")
    )
    return block_header

def mine_block(prev_block_hash: str, transactions: List[dict], total_fees: int) -> Tuple[str, int, List[str]]:
    """
    Mine a new block by finding a valid nonce that produces a block hash below the target difficulty.
    """
    coinbase_transaction = create_coinbase_transaction(total_fees)
    transactions = [coinbase_transaction] + transactions

    merkle_root = calculate_merkle_root(transactions)
    timestamp = int(time.time())
    nonce = 0

    while True:
        block_header = construct_block_header(prev_block_hash, merkle_root, timestamp, nonce)
        block_hash = double_sha256(block_header).hex()

        if block_hash < DIFFICULTY_TARGET:
            transaction_ids = [double_sha256(json.dumps(tx).encode()).hex() for tx in transactions]
            return block_hash, nonce, transaction_ids

        nonce += 1

def create_coinbase_transaction(fees: int) -> dict:
    """
    Create the coinbase transaction for the new block.
    """
    coinbase_transaction = {
        "inputs": [],
        "outputs": [{"value": BLOCK_REWARD + fees, "script": ""}],
    }
    return coinbase_transaction

def select_transactions(mempool: Dict[str, Tuple[int, Dict]]) -> List[dict]:
    """
    Select valid transactions from the mempool.
    """
    selected_transactions = []
    total_fees = 0
    block_size_limit = 1_000_000

    for tx_id, (tx_value, tx) in mempool.items():
        if validate_transaction(tx, mempool):
            tx_size = len(json.dumps(tx))
            if total_fees + tx_value <= BLOCK_REWARD and sum(len(json.dumps(tx)) for tx in selected_transactions) + tx_size <= block_size_limit:
                selected_transactions.append(tx)
                total_fees += tx_value

    return selected_transactions

def calculate_score(transactions: List[dict], total_fees: int) -> int:
    """
    Calculate the score based on the fee collected and the amount of available block space utilized.
    """
    total_size = sum(len(json.dumps(tx)) for tx in transactions)
    block_size_limit = 1_000_000  # Assuming a block size limit of 1 MB

    space_utilization_score = (total_size * 100 // block_size_limit)
    fee_score = min(total_fees // 1000, 100)  # Cap the fee score to 100

    score = space_utilization_score + fee_score
    return score

def build_mempool(mempool_dir: str) -> Dict[str, Tuple[int, Dict]]:
    """
    Build the mempool from the transaction files in the mempool directory.
    """
    mempool = {}
    for filename in os.listdir(mempool_dir):
        filepath = os.path.join(mempool_dir, filename)
        with open(filepath, "r") as file:
            transaction = json.load(file)
            tx_id = double_sha256(json.dumps(transaction).encode()).hex()
            tx_fee = sum(output.get("value", 0) for output in transaction.get("vout", []))
            mempool[tx_id] = (tx_fee, transaction)
    return mempool

def main():
    # Load transactions from the mempool directory
    mempool_dir = "mempool"
    mempool = build_mempool(mempool_dir)

    # Select transactions for the new block
    selected_transactions = select_transactions(mempool)

    if not selected_transactions:
        print("No valid transactions found in the mempool.")
        return

    # Calculate the total fees for the coinbase transaction
    total_fees = sum(tx_fee for tx_fee, _ in mempool.values())

    # Mine the new block
    prev_block_hash = "0" * 64  # Assuming a genesis block
    block_hash, nonce, transaction_ids = mine_block(prev_block_hash, selected_transactions, total_fees)

    # Calculate the score
    score = calculate_score(selected_transactions, total_fees)

    # Write the output to output.txt
    with open("output.txt", "w") as file:
        file.write(block_hash + "\n")
        coinbase_tx_id = transaction_ids[0]
        file.write(coinbase_tx_id + "\n")  # Coinbase transaction ID
        for txid in transaction_ids[1:]:
            file.write(txid + "\n")

    print(f"Block mined successfully! Score: {score}")
    print(f"Nonce: {nonce}")
    print(f"Coinbase Transaction ID: {coinbase_tx_id}")
    print(f"Total Fees: {total_fees}")

if __name__ == "__main__":
    main()