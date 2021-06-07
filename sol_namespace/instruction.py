"""
Factory functions for `solana.transaction.Transaction` instructions.
"""
from typing import Optional

from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID

from spl.name_service import name_program

from sol_namespace.name_model import NamespaceNode

def create_instruction(
    name: NamespaceNode,
    non_owner_funder: Optional[PublicKey]=None,
    ):
    """
    Generates the Create transaction instruction for this namespace node.
    """
    lamports = name.balance or 0
    # Fetch parent owner account, if necessary
    parent_owner_account = SYS_PROGRAM_ID
    if name.parent:
        parent_owner_account = name.parent.owner_account
        # parent_account = PublicKey(name.parent.account)
        parent_account = name.parent.account
    else:
        parent_account = SYS_PROGRAM_ID
    return name_program.create_name(
        name_program.CreateNameParams(
            funding_account=non_owner_funder or name.owner_account,
            hashed_name=name.hashed_name_field,
            lamports=lamports,
            space=name.data.space,
            owner_account=name.owner_account,
            class_account=name.class_account,
            parent_account=parent_account,
            parent_owner_account=parent_owner_account,
            name_program_id=name.program.id
        )
    )


def update_instruction(
        name: NamespaceNode,
        offset: int=0,
        input_data: bytes=None
        ):
    """
    Updates the data field either:
      - From offset 0 with the name data, serialized with the provided callable, or
      - From a manually specified offset and bytes.
    """
    if input_data is not None:
        assert offset + len(input_data) <= name.data.space
    if name.class_account != SYS_PROGRAM_ID:
        signer = name.class_account
    else:
        signer = name.owner_account
    return name_program.update_name(
        name_program.UpdateNameParams(
            name_account=name.account,
            offset=offset,
            input_data=input_data if input_data is not None else name.data.serialize(),
            name_update_signer=signer,
            name_program_id=name.program.id
        )
    )


def transfer_instruction(
    name: NamespaceNode,
    new_owner: PublicKey):
    return name_program.transfer_name(
        name_program.TransferNameParams(
            name_account=name.account,
            new_owner_account=new_owner,
            owner_account=name.owner_account,
            class_account=name.class_account,
            name_program_id=name.program.id
            )
        )


def delete_instruction(
    name: NamespaceNode,
    refund_to: PublicKey=None):
    return name_program.delete_name(
        name_program.DeleteNameParams(
            name_account=name.account,
            owner_account=name.owner_account,
            refund_account=refund_to or name.owner_account,
            name_program_id=name.program.id
            )
        )

