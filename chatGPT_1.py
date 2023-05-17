import tushare as ts
import backtrader as bt
import pandas as pd

# 加载数据
data = ts.get_k_data('hs300', ktype='D', start='2022-01-01', end='2022-12-31')
data = data.sort_values(by='date')
data.index = range(len(data))

# 创建回测类
class GridStrategy(bt.Strategy):
    params = (
        ('grid', 0.05),
        ('max_grid', 10),
    )

    def __init__(self):
        self.last_price = self.data.close[0]
        self.grid_num = 0
        self.order = None

    def next(self):
        if self.order:
            return

        if self.data.close[0] >= self.last_price * (1 + self.params.grid * self.grid_num) and self.grid_num < self.params.max_grid:
            self.grid_num += 1
            self.order = self.buy()
        elif self.data.close[0] < self.last_price * (1 - self.params.grid * self.grid_num):
            self.grid_num = 0
            self.order = self.sell()

    def notify_order(self, order):
        if order.status in [bt.Order.Completed]:
            self.last_price = order.executed.price
            self.order = None

# 创建回测环境
cerebro = bt.Cerebro()

# 将数据添加到回测环境
data = bt.feeds.PandasData(dataname=data)
cerebro.adddata(data)

# 添加策略到回测环境
cerebro.addstrategy(GridStrategy)

# 设置交易费用
cerebro.broker.setcommission(commission=0.05, commtype=bt.CommInfoBase.COMM_PERC, stocklike=True)

# 运行回测
cerebro.run()
