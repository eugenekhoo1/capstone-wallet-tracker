import pandas as pd
import numpy as np
import requests
from datetime import datetime
from web3 import Web3 as w3

# API Keys
web3_key = # API provider
etherscan_key = # etherscan API key

# Infura HTTP endpoint Ethereum mainnet
w3_client = w3(w3.HTTPProvider(f'https://mainnet.infura.io/v3/{web3_key}'))

# Manual maintenance of erc-20 dictionary
erc20_dict = {
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' : ['USDC', 6],
    '0xdAC17F958D2ee523a2206206994597C13D831ec7' : ['USDT', 6],
    '0x4Fabb145d64652a948d72533023f6E7A623C7C53' : ['BUSD', 18],
    '0x6B175474E89094C44Da98b954EedeAC495271d0F' : ['DAI', 18],
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' : ['WETH', 18],
    '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84' : ['stETH', 18],
    '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599' : ['WBTC', 8]
    }

def get_one_hop(address):
    blockheight = w3_client.eth.get_block('latest')['number']
    token_flows = {}
    add = address.lower()

    for token in list(erc20_dict.keys()):
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={token}&address={add}&page=1&offset=100&startblock=0&endblock={blockheight}&sort=asc&apikey={etherscan_key}"
        response = requests.get(url)
        txn_log = response.json()['result']

        onehop = {
        'inbound' : {},
        'outbound' : {}
        }

        for i in range(len(txn_log)):
            if txn_log[i]['to'] == add: # true: inbound tokens
                if txn_log[i]['from'] not in onehop['inbound'].keys(): # receiving address not in dict (first case)
                    onehop['inbound'][txn_log[i]['from']] = float(txn_log[i]['value']) / np.power(10,erc20_dict[token][1])
                    print(f"New inbound address {txn_log[i]['from']} added")
                else:
                    onehop['inbound'][txn_log[i]['from']] += float(txn_log[i]['value']) / np.power(10,erc20_dict[token][1]) # n+1 case: add token amounts
            else: # false: outbound tokens
                if txn_log[i]['to'] not in onehop['outbound'].keys(): # sending address not in dict (first case)
                    onehop['outbound'][txn_log[i]['to']] = float(txn_log[i]['value']) / np.power(10,erc20_dict[token][1])
                    print(f"New outbound address {txn_log[i]['to']} added")
                else:
                    onehop['outbound'][txn_log[i]['to']] += float(txn_log[i]['value']) / np.power(10,erc20_dict[token][1]) # n+1 case: add token amounts
        if len(onehop['inbound']) + len(onehop['outbound']) == 0:
            pass
        else:
            onehop_df = pd.DataFrame(onehop).fillna(0)
            onehop_df['net'] = onehop_df['inbound'] - onehop_df['outbound']
            token_flows[erc20_dict.get(token)[0]] = onehop_df

    return token_flows