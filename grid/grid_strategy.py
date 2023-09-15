import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
from backtrader.feeds import PandasData
import json
import tushare as ts
from function import *

'''
网格策略
'''
#现金
CASH = 30000
# 交易费
COMMISSION = 0.0003
# 两侧滑点
SLIPPAGE_PERC = 0.0000

# 159915.SZ
# 512880.SH.csv
ts_code = '512880.SH'
# 数据 时间范围
start_date = "20230101"
end_date = datetime.datetime.now().strftime('%Y%m%d')
config_file = '512880.SH.csv'
# config_file = '159915.csv'

st_date = datetime.datetime(2023, 1, 1)
ed_date = datetime.datetime(2023, 8, 1)
# ed_date = datetime.datetime(2023,6, 8)
yesterday = ed_date - datetime.timedelta(days=1)

with open(r'../data/tushare_token.json', 'r') as load_json:
    token_json = json.load(load_json)
token = token_json['token']
ts.set_token(token)
pro = ts.pro_api(token)

# 获取股票交易日历
cal_df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date, is_open='1')
trade_dates = cal_df['cal_date'].tolist()

# adj = pro.fund_adj(ts_code=ts_code,start_date='20200101',end_date=trade_dates[-1])
# print(adj)
# exit()
# 分段获取数据
segments = [trade_dates[i:i + 200] for i in range(0, len(trade_dates), 200)]
df_list = []
for segment in segments:
    df = pro.fund_daily(ts_code=ts_code, start_date=segment[-1], end_date=segment[0])
    df_list.append(df)
# 合并数据
# 数据结构： 'ts_code', 'trade_date', 'pre_close', 'open', 'high', 'low', 'close','change', 'pct_chg', 'vol', 'amount'
df = pd.concat(df_list)
df.sort_values('trade_date', inplace=True)
df['openinterest'] = df.apply(lambda x: 0, axis=1)
df['openinterest'].fillna(0)

# backtrader 要求 'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol', 'openinterest']]
df.trade_date = pd.to_datetime(df.trade_date)
df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']
df.datetime = pd.to_datetime(df.datetime)
df.index = df.datetime
df.sort_index(inplace=True)
df = df.dropna()

print(df.head(2))
print(df.tail(2))
df.to_csv("tmp3.csv")


# 自定义策略
class MyStrategy(bt.Strategy):
    params = (('config_file', config_file),
              ('printlog', True),)

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_open = self.datas[0].open
        self.data_low = self.datas[0].low
        self.data_high = self.datas[0].high
        self.order = None  # 记录订单
        self.order_list = []
        self.opened = False
        conf_df = pd.read_csv(self.params.config_file, delimiter="\t", index_col='idx')
        print(conf_df)
        conf_df.sort_values("price")
        tt = conf_df.loc[0]
        print(tt)
        print(tt['price'])
        self.configStrategy = conf_df
        self.openRow = tt
        self.currentHands = 0
        self.soltDict = {}  # 0 表示不可以操作，1：可以操作
        for index, row in self.configStrategy.iterrows():
            # print(f"index:{index},row:{row}")
            solt = {}
            if self.openRow['price'] > row['price']:  # 低于开仓初始化可以买，可以买
                solt['buy'] = 1
                solt['sell'] = 0
            if self.openRow['price'] < row['price']:  # 高于开仓初始化, hands 手位置，不可以买，可以卖
                if index <= self.openRow['hands']:
                    solt['buy'] = 0
                    solt['sell'] = 1
                else:  # 超出 部分，可以买 可以卖
                    solt['buy'] = 0
                    solt['sell'] = 1
            if self.openRow['price'] == row['price']:  # 暂时能买能卖，初始化建仓后变成，能卖不能买
                solt['buy'] = 0
                solt['sell'] = 0
            self.soltDict[row['price']] = solt
        print(self.soltDict)
        # 停止策略的区间
        self.stop_price = -1;
        self.mast_stop = False
        self.max_hands = 0

        for i in range(int(self.openRow['hands'])):
            order_amount = self.openRow['buyNum'] // self.openRow['hands']
            limitprice = self.configStrategy.loc[i + 1, 'price']
            self.log(f"buf:price:{self.openRow['price']},limitprice:{limitprice},size:{order_amount}")
            self.order = self.buy(price=self.openRow['price'], size=order_amount, exectype=bt.Order.Limit)
            # 发出止盈订单
            self.sell(price=limitprice, size=order_amount, exectype=bt.Order.Limit)

            if self.stop_price < self.openRow['price']:
                self.stop_price = self.openRow['price']
        self.opened = True
        solt = {'buy': 0, 'sell': 1}  # 初始化可以卖，不可以买
        self.soltDict[self.openRow['price']] = solt
        print(f"建仓结束")
        self.total_buy = 0
        self.total_sell = 0

    def next(self):
        # if self.data.low[0] > self.stop_price > 0:
        #     self.mast_stop=True
        #     return
        # 开仓
        if not self.opened:
            if self.data.low[0] <= self.openRow['price'] and self.data.high[0] >= self.openRow['price']:
                dt = self.datas[0].datetime.date(0)
                print(
                    f"建仓：\n{dt.isoformat()},low:{self.data.low[0]},high:{self.data.high[0]},price:{self.openRow['price']},hands:{int(self.openRow['hands'])}")
                # for i in range(int(self.openRow['hands'])):
                #     order_amount = self.openRow['buyNum'] // self.openRow['hands']
                #     limitprice = self.configStrategy.loc[i + 1, 'price']
                #     self.log(f"buf:price:{self.openRow['price']},limitprice:{limitprice},size:{order_amount}")
                #     self.order = self.buy(price=self.openRow['price'], size=order_amount, exectype=bt.Order.Limit)
                #     # 发出止盈订单
                #     self.sell(price=limitprice, size=order_amount, exectype=bt.Order.Limit)
                #
                #     if self.stop_price < self.openRow['price']:
                #         self.stop_price = self.openRow['price']
                # self.opened = True
                # solt = {'buy': 0, 'sell': 1}  # 初始化可以卖，不可以买
                # self.soltDict[self.openRow['price']] = solt
                # print(f"建仓结束")
        else:
            # self.datas[0].datetime.date(0)
            # print(f"self.data.datetime[0]{self.data.datetime.date(0)}: yesterday.date():{yesterday.date()}")
            if self.data.datetime.date(0) < yesterday.date():
                # print(f"self.data.datetime[0]{self.data.datetime[0]}")
                # 因为是T+1生效，所以用明天的数据，在今天下单

                filtered_df = self.configStrategy[(self.configStrategy['price'] >= self.data.low[1]) & (
                        self.configStrategy['price'] <= self.data.high[1])]

                # print(f" self.data.low[0]:{ self.data.low[0]}, self.data.low[1]:{ self.data.low[1]}")
                if not filtered_df.empty:
                    for index, row in filtered_df.iterrows():
                        # 只要买的solt 没有被占用，就可以买
                        price = row['price']
                        solt = self.soltDict[price]
                        # self.log(f"solt:{solt},price:{price}")
                        if solt['buy'] == 1:
                            order_amount = self.openRow['buyNum'] // self.openRow['hands']
                            if self.broker.getcash() < row['price'] * order_amount:
                                self.log(f"不能买,没有现金:当前资金{self.broker.getcash()},need:{row['price']*order_amount},price:{row['price']},order_amount:{order_amount}")
                                continue
                            else:
                                self.order = self.buy(self.datas[0], price=row['price'], size=order_amount, exectype=bt.Order.Limit)
                                # 发出止盈订单
                                # 查找self.configStrategy price=order.created.price的记录
                                current = self.configStrategy[self.configStrategy.price == row['price']]
                                rowIndex = current.index.values[0]
                                nextIdx = int(rowIndex) + 1
                                nextRow = self.configStrategy[self.configStrategy.index == nextIdx]
                                next_price = nextRow.price.values[0]
                                # order_amount =nextRow['buyNum'].values[0]
                                self.sell(price=next_price, size=order_amount, exectype=bt.Order.Limit)

                                self.log(
                                    f"create order，buy-- price:{row['price']},size:{order_amount}  sell-- price:{next_price},size:{order_amount}")

                                continue
                    # else:
                        # self.log(f"不能买：buy solt 没有了，solt:{solt},price:{row['price']}")
                        # continue
                    # 最新买的order price 低于 row[price] 卖出, 并且当前点位可以卖
                    # if len(self.order_list) > 0:
                    #     order = self.order_list[-1]
                    #     if solt['sell'] == 1:
                    #         if order.created.price < row['price']:
                    #             self.sell(self.datas[0], price=price, size=row['sellNum'])
                    #             self.log(f"sell:price:{price},size:{row['sellNum']}")
                    #             self.currentHands = self.currentHands - 1
                    #             # order pop
                    #
                    #             self.order_list.pop(-1)
                    #             # 当前点位不能卖了，order的price的点位可以买了
                    #             solt['sell'] = 0
                    #             solt['buy'] = 1
                    #             self.soltDict[price] = {'buy': 1, 'sell': 0}
                                # self.soltDict[order.created.price]['buy'] = {'buy': 1, 'sell': 0}
                        #     else:
                        #         self.log(f"不能卖：order price {order.executed.price} > grid:{row['price']} ")
                        # else:
                        #     self.log(f"不能卖，没有solt，sell:{solt},price:{row['price']}")

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    def notify_order(self, order):
        # 未被处理的订单
        # print(order.Status)
        # if order.status in [order.Submitted, order.Accepted]:
        if order.status in [order.Accepted]:
            # if order.issell():
            #
            #
            #     self.log('SELL order status:%s, Price: %.2f, Size: %d' %
            #              (order.Status[order.status],
            #                  order.created.price,
            #               order.created.size))

            # if order.isbuy():
            #     self.currentHands = self.currentHands + 1
            #     if self.max_hands < self.currentHands:
            #         self.max_hands = self.currentHands
            #     self.log(
            #         'BUY, ref:%.0f，executedPrice: %.2f,  createdPrice: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s, PositionSize:%s, hands:%s,max_hands:%s,cash:%s' %
            #         (order.ref,  # 订单编号
            #          order.executed.price,  # 成交价
            #          order.created.price,
            #          order.executed.value,  # 成交额
            #          order.executed.comm,  # 佣金
            #          order.executed.size,  # 成交量
            #          order.data._name,
            #          self.broker.getposition(self.data).size,
            #          self.currentHands,
            #          self.max_hands,
            #          self.broker.getcash()
            #          ))  # 股票名称
            #     # 买的话，created.price 不能再买了
            #     self.soltDict[order.created.price]['buy'] = 0
            #     # print(f"solt: {order.created.price} :{self.soltDict[order.created.price]}")

            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.total_buy = self.total_buy+1

                self.currentHands = self.currentHands + 1
                if self.max_hands < self.currentHands:
                    self.max_hands = self.currentHands
                self.log(
                    'BUY:executedPrice: %.2f, createdPrice: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s, PositionSize:%s, hands:%s, max_hands:%s, cash:%s, '
                    'total_buy:%s, total_sell:%s' %
                    (
                     order.executed.price,  # 成交价
                     order.created.price,
                     order.executed.value,  # 成交额
                     order.executed.comm,  # 佣金
                     order.executed.size,  # 成交量
                     order.data._name,
                     self.broker.getposition(self.data).size,
                     self.currentHands,
                     self.max_hands,
                     self.broker.getcash(),
                     self.total_buy,
                     self.total_sell,
                     ))  # 股票名称
                # 买的话，created.price 不能再买了
                self.soltDict[order.created.price]['buy'] = 0
                # print(f"solt: {order.created.price} :{self.soltDict[order.created.price]}")

            else:  # Sell
                self.currentHands = self.currentHands - 1
                self.total_sell =  self.total_sell +1
                self.log(
                    'SELL:executedPrice: %.2f,  createdPrice: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s, PositionSize:%s, hands:%s, max_hands:%s, cash:%s,'
                    'total_buy:%s, total_sell:%s' %
                    (
                     order.executed.price,
                     order.created.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size,
                     order.data._name,
                     self.broker.getposition(self.data).size,
                     self.currentHands,
                     self.max_hands,
                     self.broker.getcash(),
                     self.total_buy,
                     self.total_sell,
                     ))
                # 买=卖的话，created.price 低一位的price  又可以再买了

                # 查找self.configStrategy price=order.created.price的记录
                row = self.configStrategy[self.configStrategy.price == order.created.price]
                rowIndex = row.index.values[0]
                nextIdx = int(rowIndex) - 1
                # print(nextIdx)
                next_price = self.configStrategy[self.configStrategy.index == nextIdx].price.values[0]
                # print(next_price)
                if next_price:
                    self.soltDict[next_price]['buy'] = 1
                    # print(f"solt: {next_price} :{self.soltDict[next_price]}")


class PandasData_Extend(PandasData):
    # 现在是(open,0), ... , (openinterest,5)这6列，所以增加1
    # add the parameter to the parameters inherited from the base class
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']

    params = (
        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', -1),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )


# 读取数据

# 初始化Cerebro回测系统
cerebro = bt.Cerebro()

# 添加数据至回测系统
# data = bt.feeds.PandasData(dataname=df.set_index('datetime'))

# datafeed1 = bt.feeds.PandasData(dataname=data1, fromdate=st_date, todate=end_date)

data = PandasData_Extend(dataname=df, fromdate=st_date, todate=ed_date)

cerebro.adddata(data)
# cerebro.adddata(df.set_index('datetime'))

# 添加策略至回测系统
cerebro.addstrategy(MyStrategy, printlog=True, config_file=config_file)

# 设置初始资金
cerebro.broker.setcash(CASH)
# 佣金，双边各 0.0003
cerebro.broker.setcommission(commission=COMMISSION)
# 滑点：双边各 0.0001
cerebro.broker.set_slippage_perc(perc=SLIPPAGE_PERC)

cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
# 计算最大回撤相关指标
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
# 计算年化收益：日度收益
cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
# 计算年化夏普比率：日度收益
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True,
                    riskfreerate=0)  # 计算夏普比率
cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A')
# 返回收益率时序
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

# 运行回测系统
result = cerebro.run()

# 提取结果
print("--------------- 年化 -----------------")
print(result[0].analyzers._AnnualReturn.get_analysis())
print("--------------- 最大回撤 -----------------")
print(result[0].analyzers._DrawDown.get_analysis())
print("--------------- 收益 -----------------")
print(result[0].analyzers._Returns.get_analysis())
print("--------------- 夏普率 -----------------")
print(result[0].analyzers._SharpeRatio.get_analysis())
print("--------------- SharpeRatio_A -----------------")
print(result[0].analyzers._SharpeRatio_A.get_analysis())

# # 常用指标提取
analyzer = {}
# 提取年化收益
analyzer['年化收益率'] = result[0].analyzers._Returns.get_analysis()['rnorm']
analyzer['年化收益率（%）'] = result[0].analyzers._Returns.get_analysis()['rnorm100']
# 提取最大回撤
analyzer['最大回撤（%）'] = result[0].analyzers._DrawDown.get_analysis()['max']['drawdown'] * (-1)
# 提取夏普比率
analyzer['年化夏普比率'] = result[0].analyzers._SharpeRatio_A.get_analysis()['sharperatio']
# 日度收益率序列
ret = pd.Series(result[0].analyzers._TimeReturn.get_analysis())

print(analyzer)
# 获取回测结果
portfolio_value = cerebro.broker.getvalue()  # 总体收益
returns = (portfolio_value - 100000) / 100000  # 收益率
# max_drawdown = cerebro.broker.ge # 最大回撤
df = pd.Series(result[0].analyzers._AnnualReturn.get_analysis())
# 计算年化收益率
# start_date = data.index[0]
# end_date = data.index[-1]
# years = (end_date - start_date).days / 365
# annualized_returns = (1 + returns) ** (1 / years) - 1

# 打印结果
# print(f"最终价值：{portfolio_value-100000:.2f}")
# print(f"收益率：{returns:.2f}")

# print(f"年化收益率：{annualized_returns:.2%}")
# print(f"最大回撤：{max_drawdown:.2%}")


cerebro.plot(style='candlestick')
