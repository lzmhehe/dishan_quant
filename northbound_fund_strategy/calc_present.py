import pandas as pd
import numpy as np


# 构造一个dataFrame
# 第一列是时间，pattern yyyyMMdd，起始日期为20230101，结尾为20230512
# 第二列是数字，random 生成 1-10随机数
# DataFrame 按照时间列正序排序
# 构造第三例，本列数值为，第一行值到当前行的第二列构造一个序列
# 再构造第四列为，本行的第二列数字在第三列序列的百分比分位数



# 构造时间列
# start_date = pd.to_datetime('20230101', format='%Y%m%d')
# end_date = pd.to_datetime('20230512', format='%Y%m%d')
# date_range = pd.date_range(start_date, end_date, freq='D')
# date_column = date_range.strftime('%Y%m%d')
#
# # 构造随机数列
# random_column = np.random.randint(1, 11, len(date_range))
#
# # 构造第三列序列
# sequence_column = random_column.cumsum()
#
# # 构造第四列分位数列
# percentile_column = [np.percentile(sequence_column[:i+1], random_column[i]) for i in range(len(date_range))]
#
# # 构造DataFrame
# df = pd.DataFrame({
#     '时间': date_column,
#     '数字': random_column,
#     '序列': sequence_column,
#     '分位数': percentile_column
# })
#
# # 按时间列正序排序
# df.sort_values('时间', inplace=True)
#
# # 打印DataFrame
# print(df)

###
import pandas as pd
import numpy as np

start_date = '20230101'
end_date = '20230512'
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
length =  len(date_range)
num_list = list(np.random.randint(low=1, high=11, size=len(date_range)))
df = pd.DataFrame({
    'date': date_range,
    'num': num_list,
    # 'ser':[num_list[0:_+1] for _ in range(length)]
})
df = df.sort_values(by='date')

df['ser'] = [num_list[0:_+1] for _ in range(length)]

df['30percent'] = df.apply(lambda x: np.percentile(x['ser'], q=30), axis=1)
df['70percent'] = df.apply(lambda x: np.percentile(x['ser'], q=70), axis=1)
# df['分位数'] = df.apply(lambda x: np.percentile(x['序列'], q=(x['数字']-1)*10), axis=1)

df = df[['date', 'num', 'ser', '30percent','70percent']]
print(df)
df.to_csv("../data/percentile.csv", index=False)
# print(df)


#===
# trade_date	ggt_ss	ggt_sz	hgt	sgt	north_money	south_money
# df_funds = pd.read_csv('../data/northbound_funds.csv', parse_dates=['trade_date'])
# length = len(df_funds);
# money = list(df_funds['north_money'])
# df_funds['ser']=[money[0:_+1] for _ in range(length)]
# print(df_funds)
# df_funds.to_csv("tmp2.csv")
