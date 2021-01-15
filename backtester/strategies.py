from .brokers import Broker
from .candles import Candle


class Strategy:
    def __init__(self):
        self.current_candle = None

    def set_current_candle(self, candle: Candle):
        self.current_candle = candle

    def on_candle(self, broker: Broker):
        pass
