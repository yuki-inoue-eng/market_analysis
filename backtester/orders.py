from datetime import datetime
from enum import Enum
import instruments as ins


class Type(Enum):
    MARKET = "market"
    MARKET_IF_TOUCHED = "market_if_touched"


class ExitedType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class Side(Enum):
    SELL = "sell"
    BUY = "buy"


class Status(Enum):
    PENDING = "pending"
    CANCELED = "canceled"
    ENTERED = "entered"
    EXITED = "exited"


class InvalidExitPriceException(Exception):
    pass


class InvalidOrderCancelException(Exception):
    pass


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
        if self._side is Side.BUY and (price > stop_price or price < limit_price):
            raise InvalidExitPriceException("invalid stop_price or limit_price.")
        if self._side is Side.SELL and (price < stop_price or price > limit_price):
            raise InvalidExitPriceException("invalid stop_price or limit_price.")
        if ins.price_to_pips(self._instrument, abs(price - stop_price)) < self.MIN_STOP_DISTANCE_PIPS:
            raise InvalidExitPriceException("stop distance is narrow.")
        if ins.price_to_pips(self._instrument, abs(price - limit_price)) < self.MIN_LIMIT_DISTANCE_PIPS:
            raise InvalidExitPriceException("limit distance is narrow.")

        self.id = None
        self._price = price
        self._stop_price = stop_price
        self._limit_price = limit_price
        self._instrument = instrument
        self._side = side
        self._order_type = order_type
        self._unit = unit
        self.status = Status.PENDING

        self.activated_datetime = None
        self.entered_datetime = None
        self.closed_datetime = None
        self.entered_price = None  # 約定価格
        self.exited_price = None  # 約定価格
        self.executed_enter_price = None  # 注文実行価格
        self.executed_exited_price = None  # 注文実行価格
        self.exited_type = None

    def is_active(self):
        return self.activated_datetime is not None and (self.status is Status.PENDING or self.status is Status.ENTERED)

    @property
    def price(self):
        return self._price

    @property
    def stop_price(self):
        return self._stop_price

    @property
    def limit_price(self):
        return self._limit_price

    @property
    def instrument(self):
        return self._instrument

    @property
    def side(self):
        return self._side

    @property
    def order_type(self):
        return self._order_type

    @property
    def unit(self):
        return self._unit
