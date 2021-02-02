from datetime import datetime
from .strategies import Strategy
from .brokers import Broker
from .candles import Candle
from .recorders import Recorder
from .orders import Status
import pandas as pd
import os


class InvalidFeedException(Exception):
    pass


class Cerebro:
    def __init__(self, feed: list, strategy: Strategy, cerebro_no: int, export: bool):
        self.__candles = feed
        self.__strategy = strategy
        self.recorder = Recorder()
        self.__broker = Broker(self.recorder)
        self.cerebro_no = cerebro_no
        self.result_dir_name = "default"
        self.should_export = export

    def run(self):
        strategy = self.__strategy
        broker = self.__broker
        for candle in self.__candles:
            if candle.is_holiday():
                continue
            strategy.set_current_candle(candle)
            broker.set_current_candle(candle)
            strategy.on_candle(broker)
            broker.on_candles()
        print("completed cerebro: {}".format(self.cerebro_no))
        self.recorder.aggregate()

        if self.should_export:
            export_dir = "../result_data/trade_data/{}".format(self.result_dir_name)
            os.makedirs(export_dir, exist_ok=True)
            order_results = []
            header = ["side", "entered_price", "exited_price", "entered_datetime", "exited_datetime", "exited_type"]
            for order in self.recorder.orders.values():
                if order.status is Status.EXITED:
                    order_results.append([
                        order.side,
                        round(order.entered_price * 100000) / 100000,
                        round(order.exited_price * 100000) / 100000,
                        order.entered_datetime,
                        order.closed_datetime,
                        order.exited_type,
                    ])
            pd.DataFrame(order_results, columns=header).to_csv(export_dir + "/trades.csv", index=False)
            params = []
            for key, val in self.__strategy.params.items():
                params.append([key, val])
            pd.DataFrame(params).to_csv(export_dir + "/params.csv", index=False, header=False)
            self.recorder.make_graph().savefig(export_dir + "/graph.png")

    @staticmethod
    def convert_feed_to_candles(feed: list, date_from: datetime, date_to: datetime):
        header = feed.pop(0)  # remove header
        if header != ["DateTime", "Open", "High", "Low", "Close", "Volume"]:
            raise InvalidFeedException("invalid feed columns: invalid header: {}".format(header))
        candles = []
        for f in feed:
            canlde = Candle(f)
            if date_from <= canlde.date_time <= date_to:
                candles.append(Candle(f))
        candles = sorted(candles, key=lambda candle: candle.date_time)  # sort date_time
        return candles

# if __name__ == '__main__':
#     pass
