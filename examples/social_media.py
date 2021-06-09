"""
An example of an extremely simple social media protocol.
"""
import struct
import os
import json
import time
from pprint import pprint

from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.api import Client

from sol_namespace import name_model
from sol_namespace import operations


def _length_to_bytes(length: int):
    return struct.pack("<H", length)


def _bytes_to_length(length: bytes):
    return struct.unpack("<H", length)[0]


class SocialMediaData(name_model.NamespaceData):
    PLATFORM_NAME = "SOCIAL MEDIA PLATFORM"

class SocialMediaProfile(SocialMediaData):
    """
    Stores a username's profile, serves as the root name account
    for the user's entire namespace tree.
    """
    DATA_TYPE = b'\x00'
    MAX_LEN = 1024

    def __init__(self,
            username: str,
            data: str):
        self.field = f"{self.PLATFORM_NAME} PROFILE {username}"
        self.data = data
        self.space = len(data.encode())


    def serialize(self):
        encoded = self.data.encode()
        return self.DATA_TYPE + _length_to_bytes(len(encoded)) + encoded


    @classmethod
    def deserialize(cls, data: bytes):
        assert data[:1] == cls.DATA_TYPE, f"{data[0]} != {cls.DATA_TYPE}"
        size = _bytes_to_length(data[1:3])
        return data[2:size+2].decode()


class SocialMediaTimeline(SocialMediaData):
    """
    Stores a username's timeline, which is updated with each
    new post's data. Transaction history is thus the "timeline" of posts.
    """
    DATA_TYPE = b'\x01'
    MAX_LEN = 1024

    def __init__(self,
            username: str,
            data: str,
            timeline_name: str="default"):
        self.field = f"{self.PLATFORM_NAME} TIMELINE {username} {timeline_name}"
        self.data = data
        self.space = self.MAX_LEN
        # TODO Assert data size?


    def serialize(self):
        encoded = self.data.encode()
        return self.DATA_TYPE + _length_to_bytes(len(encoded)) + encoded


    @classmethod
    def deserialize(cls, data: bytes):
        assert data[:1] == cls.DATA_TYPE
        size = _bytes_to_length(data[1:3])
        return data[2:size+2].decode()


class SocialMediaFollow(SocialMediaData):
    """
    Represents a user following another user
    """
    DATA_TYPE = b'\x02'
    LENGTH = 33

    def __init__(self,
            username: str,
            following: PublicKey):
        account = str(following)
        self.field = f"{self.PLATFORM_NAME} FOLLOW {username} {account}"
        self.data = following
        self.space = self.LENGTH


    def serialize(self):
        return self.DATA_TYPE + bytes(data)


    @classmethod
    def deserialize(cls, data: bytes):
        assert data[:1] == cls.DATA_TYPE
        assert len(data) == cls.LENGTH
        return PublicKey(data[1:])


class SocialMediaMedia(SocialMediaData):
    """
    Represents a user's sharing some IPFS content.
    """
    DATA_TYPE = b'\x03'
    LENGTH = 65  # data-type byte + 64-byte IPFS CID

    def __init__(self,
            username: str,
            data: bytes):
        self.field = f"{self.PLATFORM_NAME} MEDIA {username} {account}"
        assert len(data) == 64
        self.data = data  # 64-byte CID
        self.space = self.LENGTH


    def serialize(self):
        # TODO Is the CID supposed to be encoded somehow?
        return self.DATA_TYPE + self.data


    @classmethod
    def deserialize(cls, data: bytes):
        assert data[:1] == cls.DATA_TYPE
        assert len(data) == cls.LENGTH
        # TODO Is this supposed to be base58 or base64 encoded?
        return data[1:]


# TODO I think this is better represented by frontend just
# embedding a txid into a timeline post.
class SocialMediaShare(SocialMediaData):
    """
    Represents a user sharing some txid.
    """
    DATA_TYPE = b'\x04'
    LENGTH = 65  # Data type + 64-byte txid

    def __init__(self,
            username: str,
            share_tx: str):
        self.field = f"{self.PLATFORM_NAME} FOLLOW {username} {share_tx}"
        self.data = share_tx
        self.space = self.LENGTH


    def serialize(self):
        return self.DATA_TYPE + bytes(self.data)


    @classmethod
    def deserialize(cls, data: bytes):
        assert data[:1] == cls.DATA_TYPE
        assert len(data) == cls.LENGTH
        return PublicKey(data[1:])


# We need an account to sign and create namespace accounts
with open(os.getenv('SOL_ACCOUNT'), 'r') as f:
    key = json.load(f)
funder = Account(key[:32])


# Initialize a client to talk to Solana devnet
client = Client("https://api.devnet.solana.com")


profile = SocialMediaProfile(
    username="rosco",
    data="## All About Rosco\nAn extremely famous individual who does things and stuff"
    )


min_lamports = client.get_minimum_balance_for_rent_exemption(SocialMediaProfile.MAX_LEN)['result']

profile_node = name_model.NamespaceNode(
    owner_account=funder.public_key(),
    data=profile,
    balance=min_lamports
    )

# print("CREATE PROFILE")
# txid = operations.create(client, profile_node, funder=funder)
# print(txid)

min_lamports = client.get_minimum_balance_for_rent_exemption(SocialMediaTimeline.MAX_LEN)['result']
timeline = SocialMediaTimeline("rosco",
        data="This is the first post on my timeline, cool!")
timeline_node = profile_node.create_child(timeline, balance=min_lamports)

# print("CREATE TIMELINE")
# txid = operations.create(client, timeline_node, funder=funder)
# print(txid)

timeline_node.data.data = "This is the second post on my timeline, even cooler!"

print("UPDATE TIMELINE")
txid = operations.update(client, timeline_node, signer=funder)
print(txid)

print("Sleeping...")
time.sleep(60)

print("Timeline data:")
print(operations.get_name_data(client, timeline_node))
