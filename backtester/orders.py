from enum import Enum
from .instruments import Instrument, price_to_pips


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


# 成行注文や決済を成行で行う場合は、指値・逆指値価格に None を入れてください
class Order:
    MIN_STOP_DISTANCE_PIPS = 5
    MIN_LIMIT_DISTANCE_PIPS = 5

    def __init__(self, instrument: Instrument,
                 side: Side,
                 order_type: Type,
                 unit: int,
                 price: float,
                 limit_price: float,
                 stop_price: float):

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
        self.memo = ""
        self.memo2 = ""
        self.memo3 = ""

        # validate limit_price and stop_price
        if self._order_type is Type.MARKET_IF_TOUCHED:
            if self._side is Side.BUY and (price < stop_price or price > limit_price):
                raise InvalidExitPriceException(
                    "invalid stop_price or limit_price: price = {}, stop = {}, limit = {}".format(price, stop_price,
                                                                                                  limit_price))
            if self._side is Side.SELL and (price > stop_price or price < limit_price):
                raise InvalidExitPriceException(
                    "invalid stop_price or limit_price: price = {}, stop = {}, limit = {}".format(price, stop_price,
                                                                                                  limit_price))
            if price_to_pips(self._instrument, abs(price - stop_price)) < self.MIN_STOP_DISTANCE_PIPS:
                raise InvalidExitPriceException("stop distance is narrow: distance = {}".format(
                    price_to_pips(self._instrument, abs(price - stop_price))))
            if price_to_pips(self._instrument, abs(price - limit_price)) < self.MIN_LIMIT_DISTANCE_PIPS:
                raise InvalidExitPriceException("limit distance is narrow: distance = {}".format(
                    price_to_pips(self._instrument, abs(price - stop_price))))

    def is_active(self):
        return self.activated_datetime is not None and (self.status is Status.PENDING or self.status is Status.ENTERED)

    def __is_win(self):
        if self.side is Side.SELL:
            return self.entered_price > self.exited_price
        if self.side is Side.BUY:
            return self.entered_price < self.exited_price

    def win_or_lose(self):
        if self.__is_win():
            return "WIN"
        else:
            return "LOSE"

    def acquired_pips(self):
        if self.side is Side.SELL:
            return price_to_pips(self.instrument, self.entered_price - self.exited_price)
        if self.side is Side.BUY:
            return price_to_pips(self.instrument, self.exited_price - self.entered_price)

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
