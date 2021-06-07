"""
High level interface for all Solana-related interactions with SPL Name Service.

Some of these are nothing but cleaned up output to RPC calls.
Others are actual blockchain transactions with potentially
many RPC calls to acquire necessary data for those transactions.

At a high level, this is the CRUD interface of our SPLNS "databasing".
"""
from base64 import b64decode
from typing import Optional, Union, Any

from solana.rpc.api import Client
from solana.rpc.exception import SolanaException
from solana.account import Account
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import SYS_PROGRAM_ID

from sol_namespace.name_model import NamespaceNode
from sol_namespace import instruction

# TODO Transfer and Delete operations


TxId = str
RawTx = bytes
Operation = Union[TxId, RawTx]


def create(
        client: Client,
        name: NamespaceNode,
        funder: Account,
        *signers: Account,
        populate: bool=True,
        raw: bool=False
        ) -> Optional[Operation]:
    """
    Create a name account on chain. By default, also populate it with data.

    Optionally, return a signed raw transaction instead of directly sending it.
    """
    tx = Transaction()
    tx.add(instruction.create_instruction(name))
    if populate:
        tx.add(instruction.update_instruction(name))
    if raw:
        tx.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']
        tx.sign(funder)
        for signer in signers:
            tx.sign(signer)
        return tx.serialize()
    # Otherwise just send the transaction
    try:
        response = client.send_transaction(tx, funder)
    except SolanaException as e:
        logs = e.data.get('data', {}).get('logs', [])
        # TODO More efficient/informative error parsing here
        if 'Program log: Instruction: Create' in logs and \
            'Program log: The given name account already exists.' in logs:
            print("Error -- Name Create: name account already exists")
        return None
    return response['result']


def update(
        client: Client,
        name: NamespaceNode,
        signer: Account,
        raw=False) -> Optional[Operation]:
    """
    Repopulate the entirety of the data under a name account.

    Optionally, return a signed raw transaction instead of directly sending it.
    """
    # Ensure the correct signer is passed in
    if name.class_account != SYS_PROGRAM_ID:
        assert signer.public_key() == name.class_account
    else:
        assert signer.public_key() == name.owner_account
    tx = Transaction()
    tx.add(instruction.update_instruction(name))
    if raw:
        tx.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']
        tx.sign(signer)
        return tx.serialize()

    response = client.send_transaction(tx, signer)
    return response['result']


def update_bytes(
        client: Client,
        name: NamespaceNode,
        signer: Account,
        input_data: bytes,
        offset: int=0,
        raw=False) -> Optional[Operation]:
    """
    Custom update to the data under a name account.
    Requires specifying the starting offset byte-index, and the raw bytes to write.

    Signer is either the owner of the account, or the class account if it's not
    default.
    """
    # Ensure the correct signer is passed in
    if name.class_account != SYS_PROGRAM_ID:
        assert signer.public_key() == name.class_account
    else:
        assert signer.public_key() == name.owner_account
    tx = Transaction()
    tx.add(instruction.update_instruction(name, offset=offset, input_data=input_data))
    if raw:
        tx.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']
        tx.sign(signer)
        return tx.serialize()

    response = client.send_transaction(tx, signer)
    return response['result']


def delete_name(
        client: Client,
        name: NamespaceNode,
        signer: Account,  # must correspond to name.owner_account
        refund_to: PublicKey=None,
        raw: bool=False) -> Optional[Operation]:
    """
    Delete a namespace node.
    """
    assert name.owner_account == signer.public_key(), "Must sign name deletion with account owner."
    tx = Transaction()
    tx.add(instruction.delete_instruction(name, refund_to=refund_to))
    if raw:
        tx.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']
        tx.sign(signer)
        return tx.serialize()

    response = client.send_transaction(tx, signer)
    return response['result']


def transfer_name(
        client: Client,
        name: NamespaceNode,
        new_owner: PublicKey,
        signer: Account,  # must correspond to name.owner_account
        class_account_signer: Account=None,
        raw: bool=False) -> Optional[Operation]:
    """
    Transfer a namespace node to a new owner.
    """
    tx = Transaction()
    tx.add(instruction.transfer_instruction(name, new_owner=new_owner))
    if raw:
        tx.recent_blockhash = client.get_recent_blockhash()['result']['value']['blockhash']
        tx.sign(signer)
        if class_account_signer is not None:
            assert name.class_account != SYS_PROGRAM_ID, "Invalid name class account signer"
            tx.sign(class_account_signer)
        return tx.serialize()

    if class_account_signer is not None:
        assert name.class_account != SYS_PROGRAM_ID, "Cannot specify class account signer on this name"
        response = client.send_transaction(tx, signer, class_account_signer)
    else:
        response = client.send_transaction(tx, signer)
    return response['result']



def get_name_data(client: Client, name: NamespaceNode) -> Any:
    """
    Look up account data, deserialize it.
    """
    response = client.get_account_info(name.account, encoding='jsonParsed')
    value = response['result']['value']
    if value is None:
        print(f"{name.account} not found")
        return None
    data = value['data'][0]
    data = b64decode(data)
    data = data[96:]
    return type(name.data).deserialize(data)


SOL_PRICE_USD = 40
BASE_AMT = 89088  # Minimum rent-exempt balance for accounts with no extra data allocation.
PER_BYTE = 696  # at 348 lamports per byte-year
LAMPORTS_PER_SOL = 100000000  # 100 million lamports = 1 SOL

def estimate_cost(
        n_bytes: int,
        sol_price_usd: float=SOL_PRICE_USD
        ) -> float:
    """
    Estimate dollar value of minimum rent-exempt balance
    to store `n_bytes` in a Solana account.
    """
    return sol_price_usd * (BASE_AMT + (n_bytes * PER_BYTE)) / LAMPORTS_PER_SOL
