import numpy as np
import pandas as pd

def frama(data, window, k=1.0):
    # 计算期间内的最高价和最低价
    high = data['High'].rolling(window=window).max()
    low = data['Low'].rolling(window=window).min()

    # 计算True Range (TR)
    tr = high - low

    # 计算市场波动性的估计
    er = tr.rolling(window=window).sum() / tr.sum()

    # 计算权重
    alpha = np.exp(-4.6 * (er - 1))
    alpha = np.clip(alpha, 0.01, 1.0)  # 确保alpha在0.01到1之间

    # 计算FRAMA
    frama = pd.Series(index=data.index)
    for i in range(window, len(data)):
        frama[i] = alpha[i] * data['Close'][i] + (1 - alpha[i]) * frama[i - 1]

    return frama

# 示例数据（用pandas DataFrame表示，包括日期、开盘价、最高价、最低价、收盘价）
data = pd.DataFrame({
    'Date': pd.date_range(start='2023-01-01', periods=100, freq='D'),
    'Open': np.random.rand(100) * 100,
    'High': np.random.rand(100) * 110,
    'Low': np.random.rand(100) * 90,
    'Close': np.random.rand(100) * 100
})

print(data)
# 设置FRAMA的周期
window = 20

# 计算FRAMA
frama_values = frama(data, window)

# 打印结果
print(frama_values)
