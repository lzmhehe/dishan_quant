import pandas as pd
import numpy as np

a=[2,1,10]
percentile = np.percentile(a,0)
print(percentile)
# trade_date	ggt_ss	ggt_sz	hgt	sgt	north_money	south_money
df_funds = pd.read_csv('../data/northbound_funds.csv', parse_dates=['trade_date'])
length = len(df_funds);
money = list(df_funds['north_money'])
df_funds['ser']=[money[0:_+1] for _ in range(length)]
print(df_funds)
df_funds.to_csv("tmp2.csv")


test_list=[]
test_list.append(1)

print(test_list)
pop = test_list.pop(-1)
print(pop)
print(test_list)

test_list.append(2)
test_list.append(3)
print(test_list)

pop = test_list.pop(-1)
print(pop)
print(test_list)