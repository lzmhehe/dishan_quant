from datetime import datetime
import backtrader as bt
import tushare as ts
import pandas as pd
from backtrader.feeds import PandasData

# tushare

print(ts.__version__)
def get_single_kdata(code, start='2023-02-01', end='2023-02-09', index=False):
    df = ts.get_k_data(code, autype='qfq', start=start, end=end, index=index)
    df['date'] = pd.to_datetime(df['date'])
    df['openinterest'] = 0
    return df[['date', 'open', 'high', 'low', 'close', 'volume', 'openinterest']]


# # yahoo
# def get_single_kdata(code, start='2020-01-01', end='2021-08-18'):
#     df = bt.feeds.YahooFinanceData(
#             dataname='AAPL',
#             fromdate=datetime.strptime(start,'%Y-%m-%d'),
#             todate=datetime.strptime(end,'%Y-%m-%d'),
#             adjclose=True,
#             adjvolume=True)
#     return df

secu_lst = ['600000', '000001','000300']
kdata = {}
for secu in secu_lst:
    kdata[secu] = get_single_kdata(secu)

print(kdata['000300'].head())

secu_lst = {'600000': {'start': '2020-01-01', 'end': '2020-07-18'},
            '000001': {'start': '2020-02-01', 'end': '2020-08-18'}}
kdata = {}
for secu in secu_lst.keys():
    kdata[secu] = get_single_kdata(secu, secu_lst[secu]['start'], secu_lst[secu]['end']).reset_index(drop=True)

print(kdata['000001'].head())

# 先拿大盘trading_dates
benchmark_start = min(secu_lst.values(), key=lambda x : x['start'])['start']
benchmark_end = max(secu_lst.values(), key=lambda x : x['end'])['end']
print(f"start: {benchmark_start}, end {benchmark_end}")

benchmark = '399905' # 中证500
kdata['benchmark'] = get_single_kdata(benchmark, benchmark_start, benchmark_end, index=True)
trading_dates = kdata['benchmark']['date'].tolist()
print(f"start: {trading_dates[0]}, end {trading_dates[-1]}")


for secu in set(kdata.keys())-set(['benchmark']):
    print(secu)
    secu_kdata = kdata['benchmark'][['date']].merge(kdata[secu],how='left')
    secu_kdata['suspend'] = 0
    secu_kdata.loc[secu_kdata['open'].isnull(), 'suspend'] = 1 # 标记为停盘日
    secu_kdata.set_index(['date'], inplace = True) # 设date为index
    end = secu_lst[secu]['end']
    secu_kdata.fillna(method='ffill',inplace = True) # start后的数据用前日数据进行补充
    secu_kdata.fillna(value = 0,inplace = True) #start前的数据用0补充
    secu_kdata.loc[(secu_kdata.index > end), 'suspend'] = 1
    print(secu_kdata)
    kdata[secu] = secu_kdata


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

def downcast(amount, lot):
    return abs(amount//lot*lot)

print(downcast(418,100))
print(downcast(-418,100))


class single_strategy(bt.Strategy):
    # 全局设定交易策略的参数
    params = (
        ('maperiod', 20),
    )

    def __init__(self):
        # 初始化交易指令
        self.order = None

        # 添加移动均线指标，内置了talib模块
        self.sma = bt.ind.SMA(self.datas[0], period=self.params.maperiod)

    # 可以不要，但如果你数据未对齐，需要在这里检验
    def prenext(self):
        pass

    def downcast(amount, lot):
        return abs(amount // lot * lot)

    def next(self):
        if self.order:  # 检查是否有指令等待执行,如果有就不执行这根bar
            return

        # 回测最后一天不进行买卖
        if self.datas[0].datetime.date(0) == end_date:
            return

            # 拿这根bar时期的所有资产价值（如果按日K数据放入，即代表今日的资产价值）
        self.log("%.2f元" % self.broker.getvalue())
        if not self.position:  # 没有持仓

            # 执行买入条件判断：收盘价格上涨突破20日均线；
            # 不要在股票剔除日前一天进行买入
            if self.datas[0].close > self.sma and data.datetime.date(1) < end_date:
                # 永远不要满仓买入某只股票
                order_value = self.broker.getvalue() * 0.98
                order_amount = downcast(order_value / self.datas[0].close[0], 100)
                self.order = self.buy(self.datas[0], size=order_amount, name=self.datas[0]._name)
                self.log(f"买{self.datas[0]._name}, price:{self.datas[0].close[0]:.2f}, amout: {order_amount}")
                # self.order = self.order_target_percent(self.datas[0], 0.98, name=self.datas[0]._name)
                # self.log(f"买{self.datas[0]._name}, price:{self.datas[0].close[0]:.2f}, pct: 0.98")
        else:

            # 执行卖出条件判断：收盘价格跌破20日均线，或者股票剔除
            if self.datas[0].close > self.sma or data.datetime.date(1) >= end_date:
                # 执行卖出
                self.order = self.order_target_percent(self.datas[0], 0, name=self.datas[0]._name)
                self.log(f"卖{self.datas[0]._name}, price:{self.datas[0].close[0]:.2f}, pct: 0")

    def log(self, txt, dt=None):
        ''' 输出日志'''
        dt = dt or self.datas[0].datetime.date(0)  # 拿现在的日期
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(f"""买入{order.info['name']}, 成交量{order.executed.size}，成交价{order.executed.price:.2f}""")
            elif order.issell():
                self.log(f"""卖出{order.info['name']}, 成交量{order.executed.size}，成交价{order.executed.price:.2f}""")
            self.bar_executed = len(self)

        # Write down: no pending order
        self.order = None



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
secu_lst = {'600000': {'start': '2020-01-01', 'end': '2020-07-18'},
            '000001': {'start': '2020-02-01', 'end': '2020-08-18'}}

kdata = GetKdatas(secu_lst).merge_period()
print(kdata)


class PandasData_Extend(PandasData):
    # Add a 'suspend' line to the inherited ones from the base class
    lines = ('suspend',)
    # 现在是(open,0), ... , (openinterest,5)这6列，所以增加1
    # add the parameter to the parameters inherited from the base class
    params = (('suspend', 6),)

    # 如果是csv文档，openinterest 在 GenericCSVData index是7，所以1
    # params = (('suspend', 8),)


cerebro = bt.Cerebro()
cerebro.addstrategy(single_strategy)
secu_lst = {'600000': {'start': '2020-01-01', 'end': '2020-07-18'}}
df = GetKdatas(secu_lst).merge_period()['600000']
data = PandasData_Extend(dataname=df, fromdate=df.index[0], todate=df.index[-1])
cerebro.adddata(data, name='600000')
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