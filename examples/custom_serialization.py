"""
Makes an example namespace tree on devnet.
"""
import os
import json
import time
from pprint import pprint

from solana.account import Account
from solana.rpc.api import Client

from sol_namespace import name_model
from sol_namespace import operations

# TODO Test on mainnet


# We need an account to sign and create namespace accounts
with open(os.getenv('SOL_ACCOUNT'), 'r') as f:
    key = json.load(f)
funder = Account(key[:32])


# Initialize a client to talk to Solana devnet
client = Client("https://api.devnet.solana.com")

# In order to look up the account info and get name data,
# the account needs to be funded.
min_lamports = client.get_minimum_balance_for_rent_exemption(0)['result']


# Making a tree
#  1) Make root node.
#    Class account = mutation auth, also factors into account keygen,
#    thus giving a guarantee of no collision with other users' namespaces
root_name = name_model.NamespaceNode(
    owner_account=funder.public_key(),
    # class_account=funder.public_key()
    data=name_model.NamespaceData(
        field="Some Fairly Important Set of Name to Color associations",
        space=0,
        data=""),
    balance=min_lamports
    )

lets_encode_this_to_the_chain = {
  "aliceblue": "#f0f8ff",
  "antiquewhite": "#faebd7",
  "aqua": "#00ffff",
  "aquamarine": "#7fffd4",
  "azure": "#f0ffff",
  "beige": "#f5f5dc",
  "bisque": "#ffe4c4",
  "black": "#000000",
  "blanchedalmond": "#ffebcd",
  "blue": "#0000ff",
  "blueviolet": "#8a2be2",
  "brown": "#a52a2a",
}
# We can just serialize the data by converting the hex values to bytes.
# Then when deserializing, we can prepend the "#" character.
# So we should just need a constant size of 3 bytes.
COLOR_NAME_SIZE = 3
min_lamports = client.get_minimum_balance_for_rent_exemption(COLOR_NAME_SIZE)['result']

#  2) You can define a custom class for easier init or for custom (de-)serialization
class ColorNameData(name_model.NamespaceData):
    """
    Custom `NamespaceData` implementation for (de-)serialization
    and a predefined constant amount of space.
    """
    def __init__(self, color_name: str, rgb_hex: str):
        self.field = color_name
        self.space = COLOR_NAME_SIZE
        self.data = rgb_hex

    def serialize(self):
        """
        Remove the "#" char, encode the hex to bytes.
        """
        return bytes.fromhex(self.data[1:])

    @classmethod
    def deserialize(cls, input_data: bytes):
        """
        Prepend the "#" char onto a hex string.
        """
        print(input_data)
        return "#" + input_data[:3].hex()


#  3) Make children nodes off of the root node.
nodes = []  # One node per entry in the colors JSON object.
for color_name, rgb_hex in lets_encode_this_to_the_chain.items():
    data = ColorNameData(color_name, rgb_hex)
    nodes.append(root_name.create_child(data=data, balance=min_lamports))


#  4) Execute Solana transactions using the Python objects that represent the Namespace tree
# Execute a "create/populate" transaction on the root node, then its children.
# You need to create parent nodes before creating any of their children.
def build_tree():
    print("Making root node first:")
    pprint(root_name.__dict__)

    txid = operations.create(client, root_name, funder=funder)
    print("Success? (txid:", txid + ")")

    print("Sleeping to ensure committment to blockchain before creating any children")
    time.sleep(20)  # Wait for RPC node to catch up.

    # Create the rest of the tree
    for node in nodes:
        print("Making this name next:")
        pprint(node.__dict__)

        txid = operations.create(client, node, funder=funder)
        print("Success? (txid:", txid + ")")


#  5) Reading the data back out is simple
def read_tree():
    print("Reading root node first:")
    pprint(root_name.__dict__)

    print(operations.get_name_data(client, root_name))

    for node in nodes:
        print("Reading this node next:")
        pprint(node.__dict__)

        print(operations.get_name_data(client, node))


# Let's build it!
# build_tree()


# Giving some time for the RPC node to catch up.

# print("Sleeping for a minute...")
# time.sleep(60)
# print()

# Let's read it!
read_tree()
