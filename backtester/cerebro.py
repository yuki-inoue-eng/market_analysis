from strategies import Strategy
from brokers import Broker
from candles import Candle
from recorders import Recorder


class InvalidFeedException(Exception):
    pass


class Cerebro:
    def __init__(self, feed: list, strategy: Strategy):
        self.__candles = self.__convert_to_candles(feed)
        self.__strategy = strategy
        self.__broker = Broker()
        self.__recorder = Recorder()

    def run(self):
        strategy = self.__strategy
        broker = self.__broker
        recorder = self.__recorder
        for candle in self.__candles:
            strategy.set_current_candle(candle)
            broker.set_current_candle(candle)
            strategy.on_candle(broker)
            broker.on_candles(recorder)

    @staticmethod
    def __convert_to_candles(feed: list):
        if feed[0] is not ["DateTime", "Open", "High", "Low", "Close", "Volume"]:
            raise InvalidFeedException("invalid feed columns.")
        feed.pop(0)  # remove header
        candles = []
        feed_list = feed
        for f in feed_list:
            candles.append(Candle(f))
        return candles


# if __name__ == '__main__':
#     pass
