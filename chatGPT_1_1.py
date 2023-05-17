from datetime import datetime
import backtrader as bt
import tushare as ts
import pandas as pd
from backtrader.feeds import PandasData


cerebro = bt.Cerebro()
# 设置初始资本为1 million
startcash = 10**6
cerebro.broker.setcash(startcash)
print(f"初始资金{cerebro.broker.getvalue()}")


class CommInfoPro(bt.CommInfoBase):
    params = (
        ('stamp_duty', 0.001),  # 印花税率
        ('stamp_duty_fe', 1),  # 最低印花税
        ('commission', 0.001),  # 佣金率
        ('commission_fee', 5),  # 最低佣金费
        ('stocklike', True),  # 股票
        ('commtype', bt.CommInfoBase.COMM_PERC),  # 按比例收
    )

    def _getcommission(self, size, price, pseudoexec):
        '''
        If size is greater than 0, this indicates a long / buying of shares.
        If size is less than 0, it idicates a short / selling of shares.
        '''

        if size > 0:  # 买入，不考虑印花税
            return max(size * price * self.p.commission, self.p.commission_fee)
        elif size < 0:  # 卖出，考虑印花税
            return max(size * price * (self.p.stamp_duty + self.p.commission), self.p.stamp_duty_fe)
        else:
            return 0  # just in case for some reason the size is 0.


cerebro.broker.addcommissioninfo(CommInfoPro())



class GetKdatas(object):
    def __init__(self, secu_lst, benchmark='000001'):
        """
        :parameter secu_lst: a dict contained stocks with starts and ends
        :parameter benchmark: the name of benchmark
        """
        self.secu_lst = secu_lst
        self.benchmark = benchmark

    @staticmethod
    def get_single_kdata(code, start='2020-01-01', end='2021-08-18', index=False):
        df = ts.get_k_data(code, autype='qfq', start=start, end=end, index=index)
        df['date'] = pd.to_datetime(df['date'])
        df['openinterest'] = 0
        return df[['date', 'open', 'high', 'low', 'close', 'volume', 'openinterest']]

    def get_all_kdata(self):
        kdata = {}
        for secu in set(self.secu_lst):
            secu_kdata = self.get_single_kdata(secu, self.secu_lst[secu]['start'], self.secu_lst[secu]['end'])
            kdata[secu] = secu_kdata.reset_index(drop=True)
        return kdata

    def merge_period(self):
        all_kdata = self.get_all_kdata()
        benchmark_start = min(self.secu_lst.values(), key=lambda x: x['start'])['start']
        benchmark_end = max(self.secu_lst.values(), key=lambda x: x['end'])['end']
        all_kdata['benchmark'] = self.get_single_kdata(self.benchmark, benchmark_start, benchmark_end,True)

        for secu in set(all_kdata.keys()) - set(['benchmark']):
            secu_kdata = all_kdata['benchmark'][['date']].merge(all_kdata[secu], how='left')
            secu_kdata['suspend'] = 0
            secu_kdata.loc[secu_kdata['open'].isnull(), 'suspend'] = 1  # 标记为停盘日
            secu_kdata.set_index(['date'], inplace=True)  # 设date为index
            end = secu_lst[secu]['end']
            secu_kdata.fillna(method='ffill', inplace=True)  # start后的数据用前日数据进行补充
            secu_kdata.fillna(value=0, inplace=True)  # start前的数据用0补充
            secu_kdata.loc[(secu_kdata.index > end), 'suspend'] = 1
            all_kdata[secu] = secu_kdata

        _ = all_kdata.pop('benchmark')
        return all_kdata
# secu_lst = {'600000': {'start': '2022-01-01', 'end': '2022-12-31'},
#             '000001': {'start': '2022-01-01', 'end': '2022-12-31'}}
#
# kdata = GetKdatas(secu_lst).merge_period()
# print(kdata)


class PandasData_Extend(PandasData):
    # Add a 'suspend' line to the inherited ones from the base class
    lines = ('suspend',)
    # 现在是(open,0), ... , (openinterest,5)这6列，所以增加1
    # add the parameter to the parameters inherited from the base class
    params = (('suspend', 6),)

    # 如果是csv文档，openinterest 在 GenericCSVData index是7，所以1
    # params = (('suspend', 8),)


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




cerebro = bt.Cerebro()
cerebro.addstrategy(GridStrategy)

secu_lst = {'000001': {'start': '2022-01-01', 'end': '2022-12-31'}}
df = GetKdatas(secu_lst).merge_period()['000001']
data = PandasData_Extend(dataname=df, fromdate=df.index[0], todate=df.index[-1])
cerebro.adddata(data, name='000001')
end_date = df.index[-1]  # 股票剔除日

# 设置初始资本为1 million
startcash = 10 ** 6
cerebro.broker.setcash(startcash)
print(f"初始资金{cerebro.broker.getvalue()}")
# 设置交易手续费
cerebro.broker.addcommissioninfo(CommInfoPro())
# 运行回测系统
cerebro.run()
# 获取回测结束后的总资金
portvalue = cerebro.broker.getvalue()
# 打印结果
print(f'结束资金: {round(portvalue, 2)}')

cerebro.plot(style='candlestick')

import numpy as np
import matplotlib.pyplot as plt
% matplotlib
inline

thestrat = thestrats[0]
pyfolio = thestrat.analyzers._pyfolio.get_analysis()


def plot_strategy(pyfolio):
    returns = pyfolio['returns'].values()
    returns = pd.DataFrame(list(zip(pyfolio['returns'].keys(), pyfolio['returns'].values())),
                           columns=['date', 'total_value'])

    sharpe = np.round(np.sqrt(252) * returns['total_value'].mean() / returns['total_value'].std(), 4)
    returns['total_value'] = returns['total_value'] + 1
    returns['total_value'] = returns['total_value'].cumprod()
    annal_rtn = np.round(returns['total_value'].iloc[-1] ** (252 / len(returns)) - 1, 4) * 100
    dd = 1 - returns['total_value'] / np.maximum.accumulate(returns['total_value'])
    end_idx = np.argmax(dd)
    start_idx = np.argmax(returns['total_value'].iloc[:end_idx])
    maxdd_days = end_idx - start_idx
    maxdd = np.round(max(dd), 4) * 100

    returns = returns.set_index('date')
    ax = returns.plot(y='total_value')
    plt.text(0.01, 0.8, f'sharpe: {sharpe:.2f}', transform=ax.transAxes)
    plt.text(0.01, 0.75, f'maxdd: {maxdd:.2f}%', transform=ax.transAxes)
    plt.text(0.01, 0.7, f'maxdd_days: {maxdd_days:}days', transform=ax.transAxes)
    plt.text(0.01, 0.65, f'annal_rtn: {(annal_rtn):.2f}%', transform=ax.transAxes)
    plt.scatter([returns.index[start_idx], returns.index[end_idx]], [returns.iloc[start_idx], returns.iloc[end_idx]],
                s=80, c='g', marker='v', label='MaxDrawdown Duration')
    plt.title('portfolio')
    plt.show()


plot_strategy(pyfolio)