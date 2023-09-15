import backtrader as bt
import pandas as pd
import datetime

import tushare as ts
import json



'''
拉取公募基金的净值数据
https://www.tushare.pro/document/2?doc_id=119
当前拉取的是
007339.OF 易方达沪深300ETF联接C	
'''

with open(r'../data/tushare_token.json','r') as load_json:
    token_json = json.load(load_json)
token = token_json['token']
ts.set_token(token)
pro = ts.pro_api(token)

df_list = []
df = pro.fund_basic(status='L')
print(df)
df_list.append(df)

df = pro.fund_basic(status='L',offset=15000,limit=15000)
df_list.append(df)
df = pd.concat(df_list)

print(df)
df.to_csv('../data/fund_basic.csv',index=False)