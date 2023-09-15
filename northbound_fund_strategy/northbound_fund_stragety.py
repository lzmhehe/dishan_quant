import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
from backtrader.feeds import PandasData

'''
信号量：北向资金
历史的北向资金由高到低排序
如果当前的北向资金落入到100-70 区间，则买入
如果落入到30-0区间，则卖出 
中间部分持有

资金用光停止买入，空仓，停止卖出
不考虑持有7天内 1.5% 的交易费
用C基金，没有交易费，管理费暂时忽略
场外基金交易，不考虑滑点

买入两种策略
1.1次现金的95%
2.分5手买入，每次20%，没有现金不再买入，没有持仓，不能卖

target ： 沪深300 |007339.OF 易方达沪深300ETF联接C
因为易方达沪深300ETF联接C 成立日期 2019年，所以使用A的基金净值，C的费用

ref:
fetch300etf.py
fetch_northbound.py

'''

# 读取数据文件
# ts_code	trade_date	close	open	high	low	pre_close	change	pct_chg	vol	amount
# df_index = pd.read_csv('../data/000300.SH.index_daily.csv', parse_dates=['trade_date'])
# ts_code,ann_date,nav_date,unit_nav,accum_nav,accum_div,net_asset,total_netasset,adj_nav,update_flag
df_index = pd.read_csv('../data/110020.OF_fund_nav.csv', parse_dates=['nav_date'])

# trade_date	ggt_ss	ggt_sz	hgt	sgt	north_money	south_money
df_funds = pd.read_csv('../data/northbound_funds.csv', parse_dates=['trade_date'])

# 合并数据
df = pd.merge(df_index, df_funds, left_on='nav_date', right_on='trade_date')

# 将数据按照时间排序
df.sort_values('trade_date', inplace=True)
# print(df.head())
# print(df.columns)
# df.to_csv("tmp1.csv")

df = df[['nav_date', 'accum_nav', 'accum_nav', 'accum_nav', 'accum_nav', 'north_money']]
df.columns = ['trade_date', 'open', 'high', 'low', 'close', 'north_money']
df.trade_date = pd.to_datetime(df.trade_date)
df.index = df.trade_date
df.sort_index(inplace=True)
# df.fillna(0.0,inplace=True)
# print(df.head())
# print(df.columns)
# df.to_csv("tmp2.csv",index=False)


length = len(df);
price_list = list(df['north_money'].fillna(0))
df['ser'] = [price_list[0:_ + 1] for _ in range(length)]
df['percent30'] = df.apply(lambda x: np.percentile(x['ser'], q=30), axis=1)
df['percent70'] = df.apply(lambda x: np.percentile(x['ser'], q=70), axis=1)


def calcBuyTag(num, percent30, percent70):
    if num >= percent70:
        return 1
    if num <= percent30:
        return 0
    else:
        return -1


def downcast(amount, lot):
    return abs(amount // lot * lot)


# 'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
df['tag'] = df.apply(lambda x: calcBuyTag(x['north_money'], x['percent30'], x['percent70']), axis=1)
# df['openinterest'] = df.apply(lambda x: 0, axis=1)
# df['openinterest'].fillna(0)
# df = df[['trade_date', 'open', 'high', 'low', "pre_close", "vol", 'openinterest', 'tag']]
# df = df[['trade_date', 'open', 'high', 'low', 'tag']]

# df.rename(columns={'trade_date': 'datetime', 'pre_close': 'close', 'vol': 'volume'}, inplace=True)
# df['datetime'] = df.apply(lambda x:  pd.to_datetime(x["datetime"], format="%Y/%m/%d"), axis=1).astype('datetime64')
# df.to_csv("tmp4.csv",index_label=False)
# print(df.columns)
('volume', -1),
('openinterest', -1),
df['volume'] = df.apply(lambda x: 10000000000, axis=1)
df['volume'].fillna(10000000000)

df['openinterest'] = df.apply(lambda x: 0, axis=1)
df['openinterest'].fillna(0)

df = df[['trade_date', 'open', 'high', 'low', 'low', 'volume', 'openinterest', "north_money", "tag"]]
df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', "north_money", "tag"]
# df.to_csv("tmp3.csv", index=False)


# 自定义策略
class MyStrategy(bt.Strategy):
    '''选股策略'''
    params = (('maperiod', 15),
              ('printlog', True),)

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_open = self.datas[0].open
        self.order = None  # 记录订单
        self.currentHands = 0
        self.order_list = []
        self.max_hands = 1

    def next(self):
        if self.data.tag[0] == 1:  # 买入信号
            if self.currentHands < self.max_hands:
                # 永远不要满仓买入某只股票
                # order_value = self.broker.getcash()/(self.max_hands-self.currentHands)
                # self.log(f"cash:{self.broker.getcash()},order_value:{order_value}")
                order_value = self.broker.getcash() * 0.95
                # order_value = 20000
                order_amount = downcast(order_value / self.datas[0].close[0], 100)
                self.order = self.buy(self.datas[0], size=order_amount, name=self.datas[0]._name)
                order = self.order
                # self.log(f"买{self.datas[0]._name}, price:{self.datas[0].close[0]:.2f}")
                # if self.order:
                #     print(f"create order.size:{order.size},order.price:{order.price}")
                self.order_list.append(order)
                # print(f"buy order list len:{len(self.order_list)}")
                # self.order = self.order_target_value(10000)
                # self.order = self.buy(size=10000)  # 买入1万元
                self.currentHands = self.currentHands + 1

            else:
                self.log("没有钱了,不能买")

        if self.data.tag[0] == 0:  # 卖出信号
            if self.currentHands > 0:
                self.currentHands = self.currentHands - 1
                # print(f"sell order list len:{len(self.order_list) } {self.order_list}")
                order = self.order_list.pop(0)
                if order:
                    self.sell(size=order.size, price=self.data.close)
                    # data = self.getdatabyname(order)
                    # if self.getposition(data).size > 0:

                # print(f"sell order:{order}")
                # order.close
                # self.order = self.sell(size=10000)  # 卖出1万元
                # self.log(f"卖{self.datas[0]._name}, price:{self.datas[0].close[0]:.2f}, pct: 0")
            else:
                self.log("没有仓位,不能卖")

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                    'BUY, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s, PositionSize:%s, hands:%s,cash:%s' %
                    (order.ref,  # 订单编号
                     order.executed.price,  # 成交价
                     order.executed.value,  # 成交额
                     order.executed.comm,  # 佣金
                     order.executed.size,  # 成交量
                     order.data._name,
                     self.broker.getposition(self.data).size,
                     self.currentHands,
                     self.broker.getcash()
                     ))  # 股票名称
            else:  # Sell
                self.log(
                    'SELL, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s, PositionSize:%s, hands:%s,cash:%s' %
                    (order.ref,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size,
                     order.data._name,
                     self.broker.getposition(self.data).size,
                     self.currentHands,
                     self.broker.getcash()
                     ))


class PandasData_Extend(PandasData):
    # Add a 'tag' line to the inherited ones from the base class
    lines = ('north_money', 'tag',)
    # 现在是(open,0), ... , (openinterest,5)这6列，所以增加1
    # add the parameter to the parameters inherited from the base class
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest', "north_money", "tag"]

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
        ('north_money', -1),
        ('tag', -1),)


# 读取数据
# data = pd.read_csv('stock_000300sh.csv', parse_dates=['trade_date'], index_col='trade_date')

# 初始化Cerebro回测系统
cerebro = bt.Cerebro()

# 添加数据至回测系统
# data = bt.feeds.PandasData(dataname=df.set_index('datetime'))
st_date = datetime.datetime(2015, 1, 1)
end_date = datetime.datetime(2023, 5, 1)
# datafeed1 = bt.feeds.PandasData(dataname=data1, fromdate=st_date, todate=end_date)

data = PandasData_Extend(dataname=df, fromdate=st_date, todate=end_date)

cerebro.adddata(data)
# cerebro.adddata(df.set_index('datetime'))

# 添加策略至回测系统
cerebro.addstrategy(MyStrategy, printlog=True)

# 设置初始资金
cerebro.broker.setcash(100000)
# 佣金，双边各 0.0003
# cerebro.broker.setcommission(commission=0.0003)
# 滑点：双边各 0.0001
# cerebro.broker.set_slippage_perc(perc=0.0001)

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

hs300_nor = [-21.63, -5.20, 27.21, 36.07, -25.31, 21.78, -11.28, 5.58]
target_nor = [-18.96, -2.43, 29.72, 35.81, -22.20, 22.63, -8.04, 6.73]
date_ser = [2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]

plData = {
    "hs300": hs300_nor,
    "300ETF": target_nor,
    "date_ser": date_ser
}
# df = pd.DataFrame(data, index = ["day1", "day2", "day3"])
data = result[0].analyzers._AnnualReturn.get_analysis()

df = pd.DataFrame(plData)
df["strategy"] = df.apply(lambda x: data.get(x["date_ser"]) * 100, axis=1)
df = df[["date_ser", "hs300", "300ETF", "strategy"]]
df = df.sort_values("date_ser")

print(df)

# 绘制策略曲线
def draw_equity_curve(df, data_dict, time='date_ser', pic_size=[16, 9], dpi=72, font_size=25):
    plt.figure(figsize=(pic_size[0], pic_size[1]), dpi=dpi)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    for key in data_dict:
        plt.plot(df[time], df[data_dict[key]], label=key)
    plt.legend(fontsize=font_size)
    plt.show()


# plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.sans-serif'] = ['SimHei']
import matplotlib

plt.rcParams['axes.unicode_minus'] = False
draw_equity_curve(df, data_dict={'沪深300': 'hs300', '易方达沪深300ETF': '300ETF', '测试收益': 'strategy'})
