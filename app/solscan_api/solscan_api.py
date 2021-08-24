import requests, os
from dotenv import load_dotenv
from app.solscan_api.db import add_update_balances

# ENV Variables
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(DOTENV_PATH)
BASE_URL = os.environ.get("SOLSCAN_BASE_URL")


class Solscan():
    def __init__(self, publicKey):
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
            if data['succcess'] == True:
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
            if bal_data['succcess'] == True:
                lamports = bal_data['data']['lamports']
                sol = lamports / 1000000000
            else:
                return {"success": False, "message": "Error occured while fetching balance."}
            #Get SOL price
            price_url = "{}/market".format(BASE_URL)
            params = {"symbol": "SOL"}
            price_resp = requests.get(price_url, params=params)
            price_data = price_resp.json()
            if price_data['success'] == True:
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