from db import get_underlying_tokens, save_tokens_price, get_solvest_tokens, update_solvest_tokens_price
import requests, os, time
from dotenv import load_dotenv

# ENV Variables
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(DOTENV_PATH)

COINCAP_URL = os.environ.get("COINCAP_PRICE_URL")

def save_sol_tokens_prices():
    try:
        all_tokens = get_underlying_tokens()
        db_data = list()
        for token in all_tokens:
            time.sleep(2)
            params = {"baseSymbol": token.symbol}
            res = requests.get(COINCAP_URL, params=params)
            print(res)
            if res.status_code == 200:
                data = res.json()
                if data['data']:
                    db_data.append({
                        "address": token.address,
                        "name": token.name,
                        "symbol": token.symbol,
                        "price": data['data'][0]['priceUsd']
                    })
        if db_data:
            save_tokens_price(db_data)
    except Exception as e:
        print(e)


def save_solvest_token_price():
    try:
        tokens = get_solvest_tokens()
        print(tokens)
        updated_price_dic = dict()
        for token in tokens:
            if token.solvest_symbol not in updated_price_dic:
                updated_price_dic[token.solvest_symbol] = 0
            updated_price_dic[token.solvest_symbol] += token.weight * token.price
        print(updated_price_dic)
        update_solvest_tokens_price(updated_price_dic)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    save_sol_tokens_prices()
    save_solvest_token_price()