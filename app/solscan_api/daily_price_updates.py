import requests, os
from db import get_tokens_for_candle_prices, add_token_daily_data
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ENV Variables
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(DOTENV_PATH)
COINCAP_PRICE_URL=os.environ.get('COINCAP_PRICE_URL')
COINCAP_CANDLE_URL=os.environ.get('COINCAP_CANDLE_URL')

def main():
    start = int((datetime.now() - timedelta(days=2)).timestamp())
    end = datetime.now().timestamp()
    tokens = get_tokens_for_candle_prices()
    for token in tokens:
        params = {"baseSymbol": token.symbol}
        price_res = requests.get(COINCAP_PRICE_URL, params=params)
        if price_res.status_code == 200:
            # print(price_res.json())
            data = price_res.json()
            params = {
                "exchange": data['data'][0]['exchangeId'],
                "baseId":  data['data'][0]['baseId'],
                "quoteId": data['data'][0]['quoteId'],
                "interval": "d1",
                "start": int(start) * 1000,
                "end": int(end) * 1000
            }
            res = requests.get(COINCAP_CANDLE_URL, params=params)
            if res.status_code == 200:
                db_data = list()
                data = res.json()
                for candle in data['data']:
                    db_data.append({
                        "address": token.address,
                        "date": (datetime.utcfromtimestamp(int(candle['period']/1000))).date(),
                        "closePrice": float(candle['close'])
                    })
                print(db_data)
                add_token_daily_data(db_data)
    return True

if __name__ == '__main__':
    main()
    exit()
