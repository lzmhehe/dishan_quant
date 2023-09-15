
import tushare as ts
import pandas as pd
import json

# 设置Tushare API访问令牌
with open(r'../data/tushare_token.json', 'r') as load_json:
    token_json = json.load(load_json)
token = token_json['token']
ts.set_token(token)
pro = ts.pro_api(token)

# 创建Tushare API连接
pro = ts.pro_api()

df = pro.moneyflow_hsgt(start_date='20180125', end_date='20180808')
print(df)

# 获取股票交易日历
cal_df = pro.trade_cal(exchange='SSE', start_date='20140101', end_date='20230531', is_open='1')
trade_dates = cal_df['cal_date'].tolist()

# 分段获取北向资金数据
segments = [trade_dates[i:i + 200] for i in range(0, len(trade_dates), 200)]
df_list = []

for segment in segments:
    # 获取北向资金数据
    # print(segment[0],segment[-1])
    df = pro.moneyflow_hsgt(start_date=segment[-1], end_date=segment[0])
    # print(df)
    df_list.append(df)

# 合并数据
df = pd.concat(df_list)
df.to_csv('../data/northbound_funds.csv')
# 打印结果
print(df)