"""
High level dataclasses for namespace trees on SPL Name Service.
"""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass

from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID
from spl.name_service import name_program as name_prog
from spl.name_service.utils import get_hashed_name


@dataclass
class NameProgram:
    """
    Name program and accompanied hardcoded hash prefix
    """
    hash_prefix: str
    id: PublicKey


default_program = NameProgram(
    hash_prefix=name_prog.NAME_PROGRAM_HASH_PREFIX,
    id=name_prog.DEVNET_NAME_PROGRAM_ID
    )
"""
The SPL Name Service listed in official Solana repos.
"""

mainnet_name_program = NameProgram(
    hash_prefix=name_prog.NAME_PROGRAM_HASH_PREFIX,
    id=name_prog.MAINNET_NAME_PROGRAM_ID
    )

@dataclass
class NamespaceData:
    """
    Namespace Data, separate from any parent/child/class or program interface concerns.
    the "name" that serves as a seed for the account name
    """
    field: str
    space: int
    data: Optional[Any]=''

    def serialize(self) -> bytes:
        """
        Defaults to `str.encode` on `self.data`.
        """
        return self.data.encode()

    @classmethod
    def deserialize(cls, raw_data: bytes) -> NamespaceData:
        """
        Defaults to `str.decode()`
        """
        return raw_data


@dataclass
class NamespaceNode:
    """
    Namespace Node, with namespace data, parent and child relations,
    and program interface data.

    - Note: min rent-exempt balance is currently 89088 + 696 * n bytes
    """
    owner_account: PublicKey
    data: NamespaceData
    parent: Optional[NamespaceNode] = None
    class_account: PublicKey = SYS_PROGRAM_ID
    program: NameProgram = default_program
    balance: Optional[int] = None  # Lamports
    # Calculated dynamically
    # hashed_name_field: bytes
    # account: PublicKey

    def __post_init__(self):
        if self.parent and self.parent.program != self.program:
            raise ValueError("Program ID must be same as parent node")
        self.hashed_name_field = get_hashed_name(
            self.program.hash_prefix,
            self.data.field)
        if self.parent:
            parent_account = self.parent.account
        else:
            parent_account = SYS_PROGRAM_ID
        self.account, _ = PublicKey.find_program_address(
            [
                self.hashed_name_field,
                bytes(self.class_account),
                bytes(parent_account)
            ],
            self.program.id
            )


    def create_child(self,
            data: NamespaceData,
            owner: Optional[PublicKey]=None,
            class_account: PublicKey=SYS_PROGRAM_ID,
            balance: Optional[int]=None,
            ) -> NamespaceNode:
        """
        Initialize a new `NamespaceNode` parented by `self`.
        """
        return NamespaceNode(
            owner_account=owner or self.owner_account,
            data=data,
            balance=balance,
            parent=self,
            class_account=class_account,
            program=self.program
        )
