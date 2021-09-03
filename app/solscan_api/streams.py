from db import get_streams, get_last_transaction, add_stream_transaction
from solana.account import Account
from solana.instruction import InstructionLayout, encode_data
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from datetime import date

payer_priv_key = [6, 208, 225, 71, 116, 134, 41, 154, 131, 204, 187, 35, 134, 162, 183, 234, 150, 55, 183, 3, 200, 108, 200, 63, 255, 114, 18, 97, 64, 187,
                  216, 26, 148, 251, 254, 212, 48, 114, 89, 246, 78, 119, 45, 9, 215, 247, 205, 215, 230, 30, 160, 207, 13, 230, 129, 121, 177, 36, 249, 105, 185, 102, 176, 33]

withdraw_payer = Account(payer_priv_key[:32])
programId = "KDr4UTEmxbX6AZexzo652VikoBoJRNGn8QafHWmyw48"

dev_4_priv = [154, 62, 175, 106, 31, 23, 233, 129, 64, 128, 83, 128, 130, 20, 41, 120, 239, 121, 227, 40, 23, 234, 77, 47, 181, 134, 89, 145, 148, 30, 166,
              194, 194, 180, 17, 248, 112, 70, 90, 93, 213, 188, 162, 44, 68, 76, 205, 121, 191, 227, 225, 177, 197, 36, 167, 249, 176, 0, 152, 10, 122, 231, 41, 53]

transfer_payer = Account(dev_4_priv[:32])

token_pub_key = PublicKey("Gmct6qXq8HvjNBJSc9QrySKZknbTqxz7QA9EXFjEn17e")
token_address_key = PublicKey("9w5RaxyUDz6f83aTtyuf4sWXkgNUd6k1sfqqKbJaEgA1")

solana_client = Client("https://api.devnet.solana.com")

# {"DB CODE for interval": "interval in days"}
STREAM_INTERVAL = {
    0: 1,
    1: 7,
    2: 30
}


def withdraw(pda: str):
    transfer_layout = InstructionLayout(idx=1, fmt="Q")
    data = encode_data(transfer_layout, 0)

    instruction = TransactionInstruction(keys=[
        AccountMeta(
            pubkey=withdraw_payer.public_key(),
            is_signer=True,
            is_writable=True
        ), AccountMeta(
            pubkey=PublicKey(pda),
            is_signer=False,
            is_writable=True
        ),
    ],
        program_id=PublicKey(programId),
        data=data
    )

    block_data = solana_client.get_recent_blockhash()

    transaction = Transaction(
        fee_payer=withdraw_payer.public_key(),
        recent_blockhash=block_data['result']['value']['blockhash']
    )

    transaction.add(instruction)
    transaction.add_signer(withdraw_payer)

    solana_client.send_transaction(transaction, withdraw_payer)

def toLamports(amount: int):
    return amount * 1000_000_000

def getTokenAccountKey(publicKey: PublicKey, token: Token):
    res = token.get_accounts(PublicKey(publicKey))
    if len(res['result']['value']) > 0:
        return res['result']['value'][0]['pubkey']
    else:
        return token.create_associated_token_account(PublicKey(publicKey))

# Transfer sBucks token to User
# args:
#  1. to: str (public address of user)
#  2. amount: int
#      - amount == dollar value of total withdrawn SOL / dollar price of one sBucks token
#      - suppose we've withdrawn 10$ worth of SOL from user's investPda, we must send 10$ worth of sBucks token to user
def transfer(to: str, amount: int):
    token = Token(solana_client, token_pub_key, TOKEN_PROGRAM_ID, transfer_payer)

    dest_key = getTokenAccountKey(PublicKey(to), token)
    res = token.transfer(
        source=token_address_key,
        dest=dest_key,
        owner=transfer_payer,
        amount=toLamports(amount)
    )
    print(res)

def main():
    today_date = date.today()
    streams = get_streams()
    for stream in streams:
        db_transaction = None
        # Check for endDate
        if stream.endTime.date() > today_date:
            # Fetch last transaction date of stream
            transaction = get_last_transaction(stream.id)
            if transaction is None:
                # Make first transaction for stream
                withdraw(stream.investPda)
                transfer(stream.publicKey, stream.totalAmount)
                db_transaction = {
                    "streamId": stream.id,
                    "date": today_date
                }
            else:
                days_since_last_transaction = (today_date - transaction.transactionTime).days
                if STREAM_INTERVAL[stream.interval] == days_since_last_transaction:
                    # Make next transaction for stream
                    withdraw(stream.investPda)
                    transfer(stream.publicKey, stream.totalAmount)
                    # Add transaction to DB
                    db_transaction = {
                        "streamId": stream.id,
                        "date": today_date
                    }
        if db_transaction:
            print("Adding transaction to DB")
            add_stream_transaction(db_transaction)

if __name__ == '__main__':
    main()
    exit()