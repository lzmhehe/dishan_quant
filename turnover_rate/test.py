from function import find_position

import pandas as pd

# 示例DataFrame
data = {'trade_date': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04', '2021-01-05'],
        'vol': [5, 3, 9, 2, 7]}
df = pd.DataFrame(data)


# 对'vol'列应用滚动窗口和自定义函数
window_size = 3
df['position'] = df['vol'].rolling(window=window_size).apply(lambda x: find_position(x))

print(df)