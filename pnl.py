import pandas as pd
import numpy as np
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import matplotlib.pyplot as plt
import requests
import psycopg2query
import json

# Run cgextras.py for cg_ethereum_token_list.json and cg_token_list.csv
with open('cg_ethereum_token_list.json' , 'r') as f:
    _token_list = json.load(f)
ethereum_token_list = json.loads(_token_list)

cg_token_df = pd.read_csv('cg_token_list.csv')

def _get_price(df):
    string = ''
    for i in df['id']:
        try:
            string += f"{i},"
        except:
            print(f"{i} not tracked by CoinGecko")
    token_id_string = string[:-1]
    token_price_list = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={token_id_string}&vs_currencies=usd&&include_market_cap=true&include_24hr_change=true&include_last_updated_at=true&precision=full").json()
    return token_price_list


def _map_current_price(df, x):
    try:
        return df[x]['usd']
    except:
        return f"NaN"

def _get_pnl(df):
    # Long positions
    long = df[['token_bought', 'token_bought_address', 'token_bought_amount', 'usd_value_at_txn']].groupby(['token_bought', 'token_bought_address']).sum().reset_index()
    
    # Short positions
    short = df[['token_sold', 'token_sold_address', 'token_sold_amount', 'usd_value_at_txn']].groupby(['token_sold', 'token_sold_address']).sum().reset_index()

    # Merge
    net = pd.merge(long, short, left_on='token_bought', right_on='token_sold', how='outer', suffixes=('_bought', '_sold'))

    # Clean dataframe
    net['token'] = np.where(net['token_bought'] == 0, net['token_sold'], net['token_bought'])
    net['token_address'] = np.where(net['token_bought_address'] == 0, net['token_sold_address'], net['token_bought_address'])

    # Merge to get current prices for PnL calculation
    pnl = pd.merge(net, cg_token_df[['platforms', 'id']], left_on='token_address', right_on='platforms', how='left').replace('NaN',np.nan).dropna()

    # Get current prices via CoinGecko API
    current_price_list = _get_price(pnl)
    pnl['current_price'] = pnl['id'].apply(lambda x: _map_current_price(current_price_list, x))

    # Net position
    pnl['net_position'] = pnl['token_bought_amount'] - net['token_sold_amount']

    # Calculate average cost of tokens bought and sold
    pnl['avg_cost_price'] = pnl['usd_value_at_txn_bought'] / pnl['token_bought_amount']
    pnl['avg_sold_price'] = pnl['usd_value_at_txn_sold'] / pnl['token_sold_amount']
    
    # Calculate pnl
    pnl['realized_pnl'] = pnl['usd_value_at_txn_sold'] - (pnl['token_sold_amount'] * pnl['avg_cost_price'])
    pnl['unrealized_pnl'] = pnl['net_position'] * (pnl['current_price'] - pnl['avg_cost_price'])
    pnl['total_pnl'] = pnl['realized_pnl'] + pnl['unrealized_pnl']

    # Round to 2dp
    pnl[['token_bought_amount', 'usd_value_at_txn_bought', 'token_sold_amount', 'usd_value_at_txn_sold', 'net_position', 'realized_pnl', 'unrealized_pnl', 'total_pnl']] =     pnl[['token_bought_amount', 'usd_value_at_txn_bought', 'token_sold_amount', 'usd_value_at_txn_sold', 'net_position', 'realized_pnl', 'unrealized_pnl', 'total_pnl']].apply(lambda x: round(x, 2))
    pnl[['avg_cost_price', 'avg_sold_price']] = pnl[['avg_cost_price', 'avg_sold_price']].apply(lambda x: round(x, 4))

    return pnl

def cross_sec_pnl(wallet, protocol):
    # Query transactions by wallet address OR use uniswapv2_1.csv
    df = psycopg2query.transactions(wallet, protocol)

    pnl = _get_pnl(df)
       
    # For HTML template
    last_10_trades = df[['time', 'token_bought', 'token_bought_amount', 'token_sold', 'token_sold_amount', 'usd_value_at_txn']].sort_values('time', ascending=False).iloc[:10].reset_index(drop=True)

    return {
        'transactions' : df,
        'realized_profit' : f"USD {round(pnl['realized_pnl'].sum(),2)}",
        'unrealized_profit' : f"USD {round(pnl['unrealized_pnl'].sum(), 2)}",
        'total_profit' : f"USD {pnl['total_pnl']}",
        'transaction_count' : df.shape[0],
        'total_volume' : f"USD {round(df['usd_value_at_txn'].sum(),2)}",
        'last_10_trades' : last_10_trades,
        'pnl' : pnl.sort_values('total_pnl', ascending=False).reset_index(drop=True)
    }