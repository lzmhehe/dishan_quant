"""
Hull Moving Average (HMA) 是一种平滑的移动平均线，它可以有效减小移动平均线在快速市场波动中的滞后性。
HMA的计算基于加权的移动平均和平滑技术。
下面是一个用Python实现Hull Moving Average的示例代码：

在这个示例中，我们首先定义了两个函数：

weighted_moving_average(data, weights) 用于计算加权移动平均。
hull_moving_average(data, period) 用于计算Hull Moving Average。
然后，我们提供了示例数据price_data和HMA的周期period。根据HMA的计算公式，
我们分别计算了三个加权移动平均（WMA）：wma1、wma2和wma3。最后，通过这三个WMA的组合计算得到HMA。

这段代码将计算Hull Moving Average并打印结果。请注意，实际应用中，你可能需要根据你的分析需求调整HMA的周期和其他参数。
"""

import numpy as np

def weighted_moving_average(data, weights):
    # return np.average(data, weights=weights)
    return np.sum(data * weights) / np.sum(weights)

def hull_moving_average(data, period):
    # print(np.sqrt(period))
    wma1 = 2 * weighted_moving_average(data, np.sqrt(period))
    wma2 = weighted_moving_average(data, period)
    wma3 = 4 * weighted_moving_average(data, np.sqrt(period / 2))
    HMA = wma1 - wma2 + wma3
    return HMA

# 示例数据
price_data = [10, 15, 20, 25, 30, 35, 40, 45, 50]
period = 14  # HMA的周期

# 计算Hull Moving Average
hma = hull_moving_average(np.array(price_data), period)

print("Hull Moving Average:", hma)
