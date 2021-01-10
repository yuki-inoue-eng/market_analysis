from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime
import pandas as pd
import backtrader as bt  # Backtrader
import backtrader.feeds as btfeed  # データ変換


class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30  # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        # print(self.data.datetime.datetime())
        if self.data.datetime.datetime() == datetime.datetime(2020, 1, 2, 12, 00, 00):
            print("aaaaaaaaaaaaa")
            enter = self.sell(exectype=bt.Order.Stop, price=108.30)
            self.buy(exectype=bt.Order.Stop, price=108.40)
            self.sell(exectype=bt.Order.Limit, price=108.25)

    def notify_order(self, order):
        print(order)
        print(self.position)
        print("")

        # if not self.position:  # not in the market
        #     if self.crossover > 0:  # if fast crosses slow to the upside
        #         self.buy()  # enter long
        #
        # elif self.crossover < 0:  # in the market & cross to the downside
        #     self.close()  # close long position


if __name__ == '__main__':
    df = pd.read_csv("../data/candles/USD_JPY_S5_2020.csv", low_memory=False, header=0,
                     names=("DateTime", "Open", "High", "Low", "Close", "Volume"))
    # 日時列をdatatime型にしてインデックスにして、元の列は削除する
    df = df.set_index(pd.to_datetime(df['DateTime'])).drop('DateTime', axis=1)
    print(df)
    data = btfeed.PandasData(dataname=df)  # PandasのデータをBacktraderの形式に変換する
    cerebro = bt.Cerebro()  # Cerebroエンジンをインスタンス化
    cerebro.adddata(data)  # データをCerebroエンジンに追加
    cerebro.addstrategy(SmaCross)  # ストラテジーを追加

    cerebro.broker.setcash(100000.0)  # 所持金を設定
    cerebro.broker.setcommission(commission=0.0005)  # 手数料（スプレッド）を0.05%に設定
    # cerebro.addsizer(bt.sizers.PercentSizer, percents=1000)  # デフォルト（buy/sellで取引量を設定していない時）の取引量を所持金に対する割合で指定する

    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Final cash Value: %.2f' % cerebro.broker.getcash())
    # cerebro.plot()
