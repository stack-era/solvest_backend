from db import get_all_tokens
import requests, time

def main():
    url = "http://api.coincap.io/v2/markets"
    all_tokens = get_all_tokens()
    for token in all_tokens:
        params = {"baseSymbol": token.symbol}
        res = requests.get(url, params=params)
        print(res)
        data = res.json()
        if data['data']:
            # print(data['data'][0])
            print(data['data'][0]['priceUsd'])

if __name__ == '__main__':
    main()