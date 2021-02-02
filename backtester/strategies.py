import math

from .brokers import Broker
from .candles import Candle
from datetime import timedelta
from datetime import datetime
from .instruments import Instrument


class Strategy:
    def __init__(self, instrument: Instrument, params: dict, order_books: dict, position_books: dict):
        self.current_candle = None
        self.instrument = instrument
        self.params = params
        self.order_books = order_books
        self.position_books = position_books
        self.sliding_minutes = 1

    def set_current_candle(self, candle: Candle):
        self.current_candle = candle

    def on_candle(self, broker: Broker):
        pass

    @staticmethod
    def __is_order_book_update_time(date_time: datetime):
        return math.floor(date_time.timestamp()) % 1200 == 0

    def is_lambda_invoke_time(self):
        dt = self.current_candle.date_time - timedelta(minutes=self.sliding_minutes)
        return self.__is_order_book_update_time(dt)

    def is_restraint_time_zone(self):
        return self.current_candle.date_time.hour == 21 or self.current_candle.date_time.hour == 20

    @staticmethod
    def cancel_all_pending_orders(broker: Broker):
        for order in broker.get_pending_orders():
            broker.cancel_order(order)

    @staticmethod
    def close_all_entered_orders(broker: Broker):
        for order in broker.get_entered_orders():
            broker.market_exit_order(order)

    def current_price(self):
        return self.current_candle.close

    def current_book_time_stamp(self):
        dt = self.current_candle.date_time - timedelta(minutes=self.sliding_minutes)
        return dt.timestamp()

    def before_book_time_stamp(self):
        return self.current_book_time_stamp() - 1200

    @staticmethod
    def __book_is_exist(book: dict, timestamp: int):
        timestamp_str = str(math.floor(timestamp))
        return timestamp_str in book and len(book[timestamp_str]["buckets"]) > 0

    def current_order_book_is_exist(self):
        return self.__book_is_exist(self.order_books, self.current_book_time_stamp())

    def before_order_book_is_exist(self):
        return self.__book_is_exist(self.order_books, self.before_book_time_stamp())

    def current_position_book_is_exist(self):
        return self.__book_is_exist(self.position_books, self.current_book_time_stamp())

    def before_position_book_is_exist(self):
        return self.__book_is_exist(self.position_books, self.before_book_time_stamp())

    def current_order_book(self):
        if self.__book_is_exist(self.order_books, self.current_book_time_stamp()):
            timestamp_str = str(math.floor(self.current_book_time_stamp()))
            return self.order_books[timestamp_str]
        return None

    def before_order_book(self):
        if self.__book_is_exist(self.order_books, self.before_book_time_stamp()):
            timestamp_str = str(math.floor(self.before_book_time_stamp()))
            return self.order_books[timestamp_str]
        return None

    def current_position_book(self):
        if self.__book_is_exist(self.position_books, self.current_book_time_stamp()):
            timestamp_str = str(math.floor(self.current_book_time_stamp()))
            return self.position_books[timestamp_str]
        return None

    def before_position_book(self):
        if self.__book_is_exist(self.position_books, self.before_book_time_stamp()):
            timestamp_str = str(math.floor(self.before_book_time_stamp()))
            return self.position_books[timestamp_str]
        return None
