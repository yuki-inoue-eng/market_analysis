from .brokers import Broker
from .candles import Candle
from .instruments import Instrument


class Strategy:
    def __init__(self, instrument: Instrument, params: dict, order_books: dict, position_books: dict):
        self.current_candle = None
        self.instrument = instrument
        self.params = params
        self.order_books = order_books
        self.position_books = position_books

    def set_current_candle(self, candle: Candle):
        self.current_candle = candle

    def on_candle(self, broker: Broker):
        pass
