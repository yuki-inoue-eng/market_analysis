from brokers import Broker


class Strategy:
    def __init__(self):
        self.__current_candle = None

    def set_current_candle(self, candle):
        self.__current_candle = candle

    def on_candle(self, broker: Broker):
        pass
