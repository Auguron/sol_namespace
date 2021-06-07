## SPL Name Service Python Library
A Pythonic interface to Solana's SPL Name Service program.
Create and modify entire namespace trees easily with a few intuitive data types.

```
from time import sleep

from solana import Account
from sol_namespace import NamespaceData, NamespaceNode, create, get_name_data

client = Client("https://api.devnet.solana.com")

funder = Account([...])

NAME_FIELD = "Example name"
DATA = b"some arbitrary data"
SIZE = len(data)

min_lamports = client.get_minimum_balance_for_rent_exemption(SIZE)['result']

# Represents an account created by SPL Name Service
node = NamespaceNode(
    owner_account=funder.public_key(),
    data=name_model.NamespaceData(
        field=NAME_FIELD,
        space=SIZE,
        data=DATA),
    balance=min_lamports
    )

# Creates, and by default also populates data
txid = create(client, node)
print(txid)

# Wait until our "create" transaction has enough confirmations to see account data
sleep(60)

data = get_name_data(client, node)
print(data)

# See example scripts for demonstration of other features.
```

To run a demo, point env var `SOL_ACCOUNT` to an airdrop-funded devnet account and run:
```
make demo
```

### SPL Name Service Overview
- a "Name" is literally any string, deterministically mapped to a specific Program-Derived Account.
- Some examples of a possible Name might include:
    - "https://auguron.com"
    - "1234 Alpine St, Bucktown, WI 12345"
    - "JohnQPublic@sol_checking_account"
    - "JohnQPublic@social"
    - "Cal Ripkin"
    - "Sylan Caryatid"
    - "Animalia/Something/Latin/Genus/Species"
    - "ISBN:1234578921478578"
- a Name account must have an owner, specified at creation, but later transferable.
- a Name can also store data, the max size of which is specified and fixed at creation. This data
  can be continually updated, so long as it does not exceed that maximum size.
- A Name can have a "Class" account, which signs the issuance of a name, as well as changes to any
  stored data(it signs updates _instead_ of the owner, not alongside them).
- A Name can have a "Parent" name account, the owner of which must sign the issuance of a name.
- The account mapped to the Name (the Name account) is deterministically generated from certain values.
- Changing/adding any one of these things changes the address that maps to the Name:
    - Name field (sh256 hash is used as seed)
    - Class account
    - Parent account
    - Program ID (e.g. point to a custom name program)

### Notable Properties
##### Closer Look at the Namespace Itself
- SPL Name Service essentially provides random associative access to data stored under any name account that might exist by the following lookup parameters:
  - (Hashed) arbitrary "name" string (i.e. some arbitrary (potentially long) string with real-world semantics)
  - A "Class" account (or 11111111111111111111111111111111)
  - A "Parent" account (or 11111111111111111111111111111111)
  - A Program ID for the specific Name Service Program in question
  - (A hash prefix that is hardcoded into the program deployed at the specified program id)
- *ALL* of the above attributes are necessary ingredients to this "random access".
- What you're randomly accessing is actually a deterministically generated account ID using those attributes.
- You can think of all of the above as possible degrees of freedom over which to create namespace trees.
- Access control policies (authority to write to data and/or create children) can be built out of: class, parent, and owner(transferable) accounts.
- A good way to think about it is:
  - Use either a parent node and/or class account to establish uniqueness of your namespace in the network.
  - Put the intuitive lookup "semantics" in the string value of the name field. 
  - To the extent that there is heirarchical or categorical relationships in your data, probably arrange data into parent/child relationships.
  - Establish an owner, and potentially a class (for mutation authority or namespace collision).
##### Native SPL Name Service Instructions:
The following are the only four atomic instructions. One common pattern might be to put a create and update instruction in the same transaction.
- Create -- Create a new name account, allocated with a certain amount of data, and a balance. No data in encoded into the account, the account is just created. This is when you specify owner/class/parent accounts
- Update -- Update the data stored under account with arbitrary raw bytes.
- Transfer -- Transfer ownership of the account to a new owner.
- Delete -- Delete the name account, and refund the balance to a specified account.
##### Close Look at Access Controls
- Create Authorities: Funder and Class and Parent (the latter two if not default)
- Update Authorities: Class if not default, otherwise Owner
- Owner Transfer Authority: Owner
- Delete Authority: Owner
- There is no Read authority -- if someone can guess the parameters to your name address, they can read it with a `getAccountInfo` JSON-RPC command.
##### CRUD Caveats
###### Creation
- Parents must be created before children (since parents are signers of name creation).
###### Read
- Accounts that are not rent-funded cannot be looked up, and therefore are not available for name lookup.
###### Update
- There are essentially two mutable properties: data content(update instruction), and owner(transfer instruction).
- Changing any of the following attributes entails deleting and rebuilding the entire subtree underneath the mutated node:
  - class
  - parent
  - allocated data space
  - program ID
  - name field
###### Delete
- Deleting a parent invalidates childrens' references to the deleted node.
- Even after deletion, the data exists permanently in the form of transaction data. But there is a loss of intuitive, random, namespace-oriented access. You need to know the relevant transaction IDs to find the data.
- Deletion can refund account funds to any other account.

### Not Good For
- Big Data (use IPFS, probably IPNS alongside it)
- Public data that changes thousands of times per day (consider an oracle instead)


### Achieving Encryption / Privacy
- Possible methods:
  - Injecting entropy into name field (downside: lose intuitive lookup).
  - Encrypt data before embedding on-chain (downside: need to manage encryption keys for each name's data).
  - Use hashes instead of direct content (downside: need to store data in the clear somewhere).
- Conclusion: Not ideal for data that you don't want in the clear. Some niche cases may will be favorable, however.


### Plausible Use Cases
- DNS
- Cert Chaining
- Directories (social media accounts, personal info links, sol accounts)
- Public Records (residential, legal)
- Game Metadata (software games, or TCGs, etc) (open-source game, assets/mechanics defined on-chain)
- Deeds, part of a non-custodial layer to NFT-based property ownership.
- "Green Check Mark" verification service.
- Social Media platform, open (de-)serialization protocols for profiles, posts, friends, likes
- Associations to IPFS that are on-chain (applicable to many of the above).
- Scientific data -- Periodic table of elements?
- File metadata (direct hash of file as "name" field)


### Architectural Notes
- You could store a merkle tree hash at the root of a tree, so that clients can know whether they need to traverse the tree to find updates.
