from pycoingecko import CoinGeckoAPI
import pandas as pd
import requests
import json
import time

# Returns token contract address : coingecko id
def get_cg_ethereum_token_list():
    response = requests.get('https://api.coingecko.com/api/v3/coins/list?include_platform=true')
    response_json = response.json()
    cg_ethereum_token_list = {}
    for i in response_json:
        if 'ethereum' in  i['platforms'].keys():
            cg_ethereum_token_list[i['platforms']['ethereum']] = i['id']
        else:
            pass
    return cg_ethereum_token_list

# Returns full token list form coingecko
def get_token_list():
    response = requests.get('https://api.coingecko.com/api/v3/coins/list?include_platform=true')
    response_json = response.json()
    cg_token_df = pd.DataFrame(response_json)
    cg_token_df['platforms'] = cg_token_df['platforms'].apply(lambda x: x.get('ethereum') if 'ethereum' in x else 'None')
    return cg_token_df

ethereum_token_list = json.dumps(get_cg_ethereum_token_list())
time.sleep(5)
token_list = get_token_list()

with open('cg_ethereum_token_list.json', 'w') as f:
    json.dump(ethereum_token_list, f)

token_list.to_csv('cg_token_list.csv')