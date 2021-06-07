"""
Demonstrating the SPL Name Service delete instruction.

Creates an SPL name, and deletes it after a minute.
"""
import os
import json
import time
from pprint import pprint

from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client

from spl.name_service.name_program import MAINNET_NAME_PROGRAM_ID

from sol_namespace import name_model
from sol_namespace import operations


# We need an account to sign and create namespace accounts
with open(os.getenv('SOL_ACCOUNT'), 'r') as f:
    key = json.load(f)
funder = Account(key[:32])

# Initialize a client to talk to Solana devnet
DEVNET = "https://api.devnet.solana.com"
ENDPOINT = os.getenv("SOL_ENDPOINT", DEVNET)
client = Client(ENDPOINT)

# Initialize some data we'll use to make a NamespaceNode
FIELD = "A name that will be deleted"
DATA = "Hello world!"
SIZE = len(DATA)
min_lamports = client.get_minimum_balance_for_rent_exemption(SIZE)['result']

# If client is connected to mainnet, use that SPL name program instead.
program = name_model.default_program
if client._provider.endpoint_uri == DEVNET:
    program = name_model.mainnet_name_program

# Create a NamespaceNode, which is a Python object that represents
# an SPL Name Service account.
name = name_model.NamespaceNode(
    owner_account=funder.public_key(),
    data=name_model.NamespaceData(
        field=FIELD,
        space=SIZE,
        data=DATA),
    balance=min_lamports,
    program=program
    )

# Execute program instructions on chain
txid = operations.create(client, name, funder=funder)
print(txid)
print("Sleeping to allow Solana network to catch up with new account info")
time.sleep(60)  # 60sec is probably overkill here but fine for demo
print("Querying for data on chain:")
print(operations.get_name_data(client, name))
print("Deleting...")
txid = operations.delete_name(client, name, signer=funder)
print(txid)
