import time

from csv import reader
from backtester.cerebro import Cerebro
from backtester.strategies import Strategy
from backtester.brokers import Broker


class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()

    def on_candle(self, broker: Broker):
        pass
        # print(self.current_candle.date_time)


if __name__ == "__main__":
    with open("../data/candles/NZD_USD_S5_2020.csv", "r") as read_obj:
        feed = list(reader(read_obj))
    my_strategy = MyStrategy()
    cerebro = Cerebro(feed, my_strategy)
    print("Start back test.")
    start = time.time()
    cerebro.run()
    print("Execution time: {}".format(time.time() - start))
    print("Total number of trades: {}".format(cerebro.recorder.total_number_of_trades))
