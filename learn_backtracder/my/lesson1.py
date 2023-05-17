import backtrader as bt # 导入 Backtrader

# 实例化 cerebro
cerebro = bt.Cerebro()
# 打印初始资金
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
# 启动回测
cerebro.run()
# 打印回测完成后的资金
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
# Starting Portfolio Value: 10000.00
# Final Portfolio Value: 10000.00