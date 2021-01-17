from datetime import timedelta
from .strategies import Strategy
from .brokers import Broker
from .candles import Candle
from .recorders import Recorder
from .orders import Status
import math


class InvalidFeedException(Exception):
    pass


class Cerebro:
    def __init__(self, feed: list, strategy: Strategy):
        self.__candles = self.__convert_feed_to_candles(feed)
        self.__strategy = strategy
        self.recorder = Recorder()
        self.__broker = Broker(self.recorder)

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

        # TODO: trade log
        for order in self.recorder.orders.values():
            if order.status is Status.EXITED:
                print("side:{} entered_price:{} exited_price:{}  entered:{}  exited:{}  exitedType:{}  memo:{} memo2:{} memo3:{}".format(
                    order.side,
                    round(order.entered_price*100000)/100000,
                    round(order.exited_price*100000)/100000,
                    order.entered_datetime,
                    order.closed_datetime,
                    order.exited_type,
                    order.memo,
                    order.memo2,
                    order.memo3,
                ))

    @staticmethod
    def __convert_feed_to_candles(feed: list):
        header = feed.pop(0)  # remove header
        if header != ["DateTime", "Open", "High", "Low", "Close", "Volume"]:
            raise InvalidFeedException("invalid feed columns: invalid header: {}".format(header))
        candles = []
        for f in feed:
            candles.append(Candle(f))
        candles = sorted(candles, key=lambda candle: candle.date_time)  # sort date_time
        return candles

# if __name__ == '__main__':
#     pass
