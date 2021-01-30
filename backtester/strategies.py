from .brokers import Broker
from .candles import Candle


class Strategy:
    def __init__(self, params: dict):
        self.current_candle = None
        self.params = params

    def set_current_candle(self, candle: Candle):
        self.current_candle = candle

    def on_candle(self, broker: Broker):
        pass
