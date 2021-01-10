from enum import Enum

import instruments as ins


class Type(Enum):
    MARKET = "market"
    MARKET_IF_TOUCHED = "market_if_touched"


class Side(Enum):
    SELL = "sell"
    BUY = "buy"


class Status(Enum):
    PENDING = "pending"
    CANCELED = "canceled"
    ENTERED = "entered"
    EXITED = "exited"


class Order:
    MIN_STOP_DISTANCE_PIPS = 5
    MIN_LIMIT_DISTANCE_PIPS = 5

    def __init__(self, instrument: ins.Instrument,
                 side: Side,
                 order_type: Type,
                 unit: int,
                 price: float,
                 limit_price: float,
                 stop_price: float):

        # validate limit_price and stop_price
        if self.__side == Side.BUY and (price > stop_price or price < limit_price):
            pass  # エラーを返す。不正な利確、損切り設定
        if self.__side == Side.SELL and (price < stop_price or price > limit_price):
            pass  # エラーを返す。不正な利確、損切り設定
        if ins.price_to_pips(self.__instrument, abs(price - stop_price)) < self.MIN_STOP_DISTANCE_PIPS:
            pass  # エラーを返す。ストップ幅が足りない
        if ins.price_to_pips(self.__instrument, abs(price - limit_price)) < self.MIN_LIMIT_DISTANCE_PIPS:
            pass  # エラーを返す。リミット幅が足りない

        self.__id = None
        self.__price = price
        self.__limit_price = limit_price
        self.__stop_price = stop_price
        self.__instrument = instrument
        self.__side = side
        self.__order_type = order_type
        self.__unit = unit
        self.__status = Status.PENDING

    def get_order_id(self):
        return self.__id

    # broker に登録する時に呼び出してください
    def set_order_id(self, order_id: int):
        self.__id = order_id

    def get_status(self):
        return self.__status

    def set_status(self, status: Status):
        self.__status = status

    def is_active(self):
        return self.__status == Status.PENDING or self.__status == Status.ENTERED
