import hashlib
import json
import os
from collections import OrderedDict
import sys

# Transaction validation
def validate_transaction(transaction):
    if 'inputs' not in transaction or 'outputs' not in transaction:
        return False

    inputs = transaction.get('inputs', [])
    outputs = transaction.get('outputs', [])

    if not inputs or not outputs:
        return False

    input_sum = sum(inp.get('value', 0) for inp in inputs)
    output_sum = sum(out.get('value', 0) for out in outputs)
    if input_sum < output_sum:
        return False

    return True

# Construct block header
def construct_block_header(prev_block_hash, merkle_root, timestamp, difficulty_target, nonce):
    header = OrderedDict([
        ('version', 1),
        ('prev_block_hash', bytes.fromhex(prev_block_hash)),
        ('merkle_root', bytes.fromhex(merkle_root)),
        ('timestamp', timestamp),
        ('difficulty_target', difficulty_target),
        ('nonce', nonce)
    ])
    header_bytes = b''.join(
        str(value).encode() if isinstance(value, int) else
        value.encode() if isinstance(value, str) else
        value
        for value in header.values()
    )
    return header_bytes

# Construct coinbase transaction
def construct_coinbase_transaction(block_height, fees):
    coinbase_tx = {
        'txid': 'coinbase_tx',
        'inputs': [{'value': 50 + fees}],
        'outputs': [{'value': 50 + fees}]
    }
    return coinbase_tx

# Calculate merkle root
def calculate_merkle_root(transactions):
    tx_hashes = [hashlib.sha256(json.dumps(tx).encode()).hexdigest() for tx in transactions]

    while len(tx_hashes) > 1:
        new_hashes = []
        for i in range(0, len(tx_hashes), 2):
            hash1 = tx_hashes[i]
            hash2 = tx_hashes[i + 1] if i + 1 < len(tx_hashes) else hash1
            new_hashes.append(hashlib.sha256((hash1 + hash2).encode()).hexdigest())
        tx_hashes = new_hashes

    return tx_hashes[0]

# Mine block
def mine_block(mempool_transactions, prev_block_hash, difficulty_target):
    valid_transactions = [tx for tx in mempool_transactions if validate_transaction(tx)]
    fees = sum(sum(inp.get('value', 0) for inp in tx.get('inputs', [])) - sum(out.get('value', 0) for out in tx.get('outputs', [])) for tx in valid_transactions)
    block_height = 1
    coinbase_tx = construct_coinbase_transaction(block_height, fees)
    merkle_root = calculate_merkle_root([coinbase_tx] + valid_transactions)
    nonce = 0
    timestamp = 1234567890

    while True:
        block_header = construct_block_header(prev_block_hash, merkle_root, timestamp, difficulty_target, nonce)
        block_hash = hashlib.sha256(block_header).hexdigest()
        if int(block_hash, 16) < difficulty_target:
            break
        nonce += 1

    return block_header.hex(), coinbase_tx, [tx['txid'] for tx in valid_transactions]

# Load transactions from mempool directory
def load_transactions(mempool_dir):
    transactions = []
    for filename in os.listdir(mempool_dir):
        filepath = os.path.join(mempool_dir, filename)
        with open(filepath, 'r') as file:
            transactions.append(json.load(file))
    return transactions

# Write output to file
def write_output(block_header, coinbase_tx, valid_transactions, output_file):
    with open(output_file, 'w') as file:
        file.write(block_header + '\n')
        file.write(json.dumps(coinbase_tx) + '\n')
        file.write('\n'.join(valid_transactions))

# Main function
def main():
    try:
        difficulty_target = 0x0000ffff00000000000000000000000000000000000000000000000000000000
        block_height = 1

        mempool_dir = 'mempool'
        mempool_transactions = load_transactions(mempool_dir)

        prev_block_hash = '0' * 64
        block_header, coinbase_tx, valid_transactions = mine_block(mempool_transactions, prev_block_hash, difficulty_target)

        output_file = 'output.txt'
        write_output(block_header, coinbase_tx, valid_transactions, output_file)

    except KeyboardInterrupt:
        print("Mining interrupted. Exiting...")
        sys.exit(0)

if __name__ == '__main__':
    main()
