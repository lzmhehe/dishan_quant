def weighted_moving_average(data, weights):
    """
    计算加权移动平均

    参数:
    data (list): 包含数据点的列表
    weights (list): 包含权重的列表，长度应与data相同

    返回:
    float: 加权移动平均值
    """
    if len(data) != len(weights):
        raise ValueError("数据点和权重列表的长度必须相同")

    weighted_sum = sum(data[i] * weights[i] for i in range(len(data)))
    total_weight = sum(weights)

    if total_weight == 0:
        raise ValueError("权重总和不能为零")

    weighted_average = weighted_sum / total_weight
    return weighted_average

# 示例数据
data_points = [10, 12, 14, 16, 18]
# 示例权重，这里使用递减的权重，最近的数据点权重较高
weights = [0.2, 0.3, 0.2, 0.1, 0.2]


# 计算加权移动平均
wma = weighted_moving_average(data_points, weights)
print("加权移动平均:", wma)

####### ##### case 2:
import numpy as np

# 示例数据
data = data_points  # 这里假设有5个数据点
weights = weights    # 自定义权重，长度需与数据点相同

# 计算加权移动平均
wma = np.average(data, weights=weights)

print("加权移动平均:", wma)