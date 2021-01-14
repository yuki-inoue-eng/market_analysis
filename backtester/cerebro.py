from strategies import Strategy
from brokers import Broker
from candles import Candle
from recorders import Recorder


class InvalidFeedException(Exception):
    pass


class Cerebro:
    def __init__(self, feed: list, strategy: Strategy):
        self.__candles = self.__convert_feed_to_candles(feed)
        self.__strategy = strategy
        self.__broker = Broker(self.__recorder)
        self.__recorder = Recorder()

    def run(self):
        strategy = self.__strategy
        broker = self.__broker
        for candle in self.__candles:
            strategy.set_current_candle(candle)
            broker.set_current_candle(candle)
            strategy.on_candle(broker)
            broker.on_candles()

    @staticmethod
    def __convert_feed_to_candles(feed: list):
        header = feed.pop(0)  # remove header
        if header is not ["DateTime", "Open", "High", "Low", "Close", "Volume"]:
            raise InvalidFeedException("invalid feed columns.")
        candles = []
        for f in feed:
            candles.append(Candle(f))
        candles = sorted(candles, key=lambda x: x[0])  # sort date_time
        return candles


# if __name__ == '__main__':
#     pass
