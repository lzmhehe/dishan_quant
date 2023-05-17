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


pro = ts.pro_api()
df = pro.fund_nav(ts_code='110020.OF')
df.sort_values('nav_date', inplace=True)

print(df)
df.to_csv('../data/007339.OF_fund_nav.csv',index=False)