
import pandas as pd
from function import *
df = pd.read_csv('159915.csv',delimiter="\t",index_col='idx')

print(df)
df.sort_values("price")
tt = df.loc[0]
print(tt)
print(tt['price'])

# 示例用法
my_list = [5, 3, 9, 2, 7, 4]
minimum = 3
maximum = 7

values_between = find_values_between(minimum, maximum, my_list)
print(f"在 {minimum} 和 {maximum} 之间的元素: {values_between}")

# 创建示例DataFrame
data = {'idx': [1, 2, 3, 4, 5],
        'price': [10.5, 12.3, 9.8, 11.2, 13.5],
        'hands': [100, 200, 150, 300, 250]}
df = pd.DataFrame(data)

# 输入最大值和最小值
minimum = 10
maximum = 11

# 根据条件筛选DataFrame记录
filtered_df = df[(df['price'] >= minimum) & (df['price'] <= maximum)]
print(filtered_df)



# df有两列，idx，price，查找price=入参p的这一行的上一行


# 创建示例 DataFrame
data = {'idx': ['1', '2', '3', '4'],
        'price': [10, 20, 30, 40]}
df = pd.DataFrame(data)

# 定义给定参数p
p = 30
print(df.loc[df['price'] == p]['idx'].iloc[0])
print(df.loc[df['price'] == p]['idx'].index)
row_idx= df.loc[df['price'] == p]['idx'].iloc[0]

print(row_idx)
prev_row = df.loc[df["idx"]==str(int(row_idx)-1)]

print(prev_row)


def sortOrderByPrice(lst) :
    return sorted(lst, key=lambda order: order.price)

Status = [
    'Created', 'Submitted', 'Accepted', 'Partial', 'Completed',
    'Canceled', 'Expired', 'Margin', 'Rejected',
]

print(Status[1])