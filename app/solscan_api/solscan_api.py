import requests, os, time
from dotenv import load_dotenv
from .db import add_update_balances, add_update_tokens
from datetime import datetime, timedelta

# ENV Variables
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(DOTENV_PATH)
BASE_URL = os.environ.get("SOLSCAN_BASE_URL")
TOKENS_URL = os.environ.get("SOLANA_TOKENS_URL")
COINCAP_URL = os.environ.get("COINCAP_PRICE_URL")


class Solscan():
    def __init__(self, publicKey = None):
        self.publicKey = publicKey

    def update_balances_in_db(self, userId):
        try:
            db_data = list()
            url = "{}/account/tokens".format(BASE_URL)
            params = {
                "address": self.publicKey,
                "price": 1
            }
            resp = requests.get(url, params=params)
            data = resp.json()
            if data['succcess']:
                for row in data["data"]:
                    db_data.append({
                        "userId": userId,
                        "tokenAccount": row["tokenAccount"],
                        "tokenName": row["tokenName"],
                        "tokenSymbol": row["tokenSymbol"],
                        "tokenIcon": row["tokenIcon"],
                        "priceUsdt": row["priceUsdt"] if "priceUsdt" in row else None,
                        "tokenAmountUI": row["tokenAmount"]["uiAmount"]
                    })
            else:
                return {"success": False, "message": "Error occured while Updating balacnes in DB"}
            status = add_update_balances(db_data)
            if status:
                return {"success": True, "message": "Updated balacnes in DB"}
            else:
                return {"success": False, "message": "Error occured while Updating balacnes in DB"}
        except Exception as e:
            print(e)
            return {"success": False, "message": "Error occured while Updating balacnes in DB"}

    def get_solana_balance(self):
        try:
            # Get account balance
            bal_url = "{}/account".format(BASE_URL)
            params = {"address": self.publicKey}
            bal_resp = requests.get(bal_url, params=params)
            bal_data = bal_resp.json()
            if bal_data['succcess']:
                lamports = bal_data['data']['lamports']
                sol = lamports / 1000000000
            else:
                return {"success": False, "message": "Error occured while fetching balance."}
            #Get SOL price
            price_url = "{}/market".format(BASE_URL)
            params = {"symbol": "SOL"}
            price_resp = requests.get(price_url, params=params)
            price_data = price_resp.json()
            if price_data['success']:
                price = price_data['data']['priceUsdt']
            else:
                return {"success": False, "message": "Error occured while fetching balance."}

            account_sol_amount = price * sol
            response = {
                "success": True,
                "SOLbalance": round(sol, 4),
                "USDTbalance": round(account_sol_amount, 2),
                "SOLcurrPrice": price
            }
            return response
        except Exception as e:
            print(e)
            return {"success": False, "message": "Error occured while fetching balance."}

    def get_tokens(self, limit, offset):
        try:
            url = "{}/tokens".format(BASE_URL)
            params = {"limit": limit, "offset": offset}
            token_resp = requests.get(url, params=params)
            token_data = token_resp.json()
            if token_data['succcess']:
                return token_data['data']
            else:
                return {"success": False, "message": "Error occured while fetching tokens."}
        except Exception as e:
            print(e)
            return {"success": False, "message": "Error occured while fetching tokens."}

    def save_tokens(self):
        try:
            db_data = list()
            url = TOKENS_URL
            tokens_response = requests.get(url)
            if tokens_response.status_code == 200:
                data = tokens_response.json()
                for token in data['tokens']:
                    if token['chainId'] == 101:
                        priceAvailable = False
                        params = {"baseSymbol": token['symbol']}
                        price_res = requests.get(COINCAP_URL, params=params)
                        print(price_res)
                        price_res = price_res.json()
                        if price_res['data']:
                            priceAvailable = True
                        db_data.append({
                            "address": token['address'],
                            "chainId": token['chainId'],
                            "decimals": token['decimals'],
                            "logoURI": token['logoURI'] if 'logoURI' in token else None,
                            "name": token['name'],
                            "symbol": token['symbol'],
                            "priceAvailable": priceAvailable
                        })
                if add_update_tokens(db_data) != False:
                    return {"success": True, "message": "Updated tokens in database."}
                else:
                    return {"success": False, "message": "Error occured while saving tokens"}
            else:
                return {"success": False, "message": "Error occured while saving tokens"}
        except Exception as e:
            print(e)
            return {"success": False, "message": "Error occured while saving tokens"}

    def save_historical_portfolio(self, userId):
        # Get transactions, loop through them to find token chaneges and save to db
        one_year_ago_epoch = int((datetime.now() - timedelta(days=365)).timestamp())
        print(one_year_ago_epoch)
        transactions = True
        previous_tx_hash = None
        transactions_url = "{}/account/transaction".format(BASE_URL)
        details_url = "{}/transaction".format(BASE_URL)
        tx_params = {'address': self.publicKey}
        tmp_balances = dict()
        db_data = list()
        # while transactions:
        #     # transactions var will be False if no more transactions available or if one year transactions are parsed
        #     if previous_tx_hash:
        #         tx_params['before'] = previous_tx_hash
        #     transactions_resp = requests.get(transactions_url, params=tx_params)
        #     print(transactions_resp)
        #     # print(transactions_resp.text)
        #     print(transactions_resp.headers)
        #     transactions_data = transactions_resp.json()
        #     # time.sleep(2)
        #     if transactions_data['succcess'] and transactions_data['data']:
        #         for tx in transactions_data['data']:
        #             if tx['blockTime'] > one_year_ago_epoch:
        #                 # Set previous_tx_hash
        #                 previous_tx_hash = tx['txHash']
        #                 params = {'tx': tx['txHash']}
        #                 detail_resp = requests.get(details_url, params=params)
        #                 print(detail_resp)
        #                 print(detail_resp.headers)
        #                 # print(detail_resp.text)
        #                 detail_data = detail_resp.json()
        #                 # time.sleep(1)
        #                 if 'txStatus' in detail_data and detail_data['txStatus'] == 'finalized':
        #                     for accounts in detail_data['inputAccount']:
        #                         if accounts['account'] == self.publicKey:
        #                             if 'SOL' not in tmp_balances or tmp_balances['SOL'] != accounts['postBalance']:
        #                                 db_data.append({
        #                                     "userId": userId,
        #                                     "account": self.publicKey,
        #                                     "balanceTimestamp": tx['blockTime'],
        #                                     "token": "SOL",
        #                                     "balance": accounts['postBalance']
        #                                 })
        #                             tmp_balances['SOL'] = accounts['postBalance']
        #                     for token in detail_data['tokenBalanes']:
        #                         name = "{}-{}".format(token['account'], token['token']['symbol'])
        #                         if name not in tmp_balances or tmp_balances[name] != token['amount']['postAmount']:
        #                             db_data.append({
        #                                 "userId": userId,
        #                                 "account": token['account'],
        #                                 "balanceTimestamp": tx['blockTime'],
        #                                 "token": token['token']['symbol'],
        #                                 "balance": (int(token['amount']['postAmount']) / (10 * token['token']['decimals']))
        #                             })
        #                         tmp_balances[name] = token['amount']['postAmount']
        #             else:
        #                 transactions = False
        #                 break
        # print(db_data)
        url = "https://prod-api.solana.surf/v1/account/Bxp8yhH9zNwxyE4UqxP7a7hgJ5xTZfxNNft7YJJ2VRjT/transactions?"
        params = {"before": "74Bcv1Aw7r3BG68Tu2tmLrLBV7iWi7UjtzgJ76Ly3NWCL38dkL3D6xCTAeX43zfgGnxBztHvwvLnPttLNoDKnGy+"}
        for i in range(1000):
            resp = requests.get(url, params=params)
            print(resp)
            print(resp.json())
