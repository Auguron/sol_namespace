"""
Transfer ownership of a name from one owner account to another.
"""
import os
import json
import time
from pprint import pprint

from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client

from sol_namespace import name_model
from sol_namespace import operations


# We need an account to sign and create namespace accounts
with open(os.getenv('SOL_ACCOUNT'), 'r') as f:
    key = json.load(f)
funder = Account(key[:32])

# We need an account to sign and create namespace accounts
with open(os.getenv('SOL_ACCOUNT2'), 'r') as f:
    key = json.load(f)
account2 = Account(key[:32])


# Initialize a client to talk to Solana devnet
client = Client("https://api.devnet.solana.com")

FIELD = "An SPL Name that will be transferred!"
DATA = "Hello world!"
SIZE = len(DATA)
min_lamports = client.get_minimum_balance_for_rent_exemption(SIZE)['result']

name = name_model.NamespaceNode(
    owner_account=funder.public_key(),
    data=name_model.NamespaceData(
        field=FIELD,
        space=SIZE,
        data=DATA),
    balance=min_lamports
    )

txid = operations.create(client, name, funder=funder)
print(txid)

print("Sleeping to allow Solana network to catch up with new account info")
time.sleep(60)

print("Data on chain:")
print(operations.get_name_data(client, name))

print("transferring...")
txid = operations.transfer_name(client, name, new_owner=account2.public_key(), signer=funder)
print(txid)
