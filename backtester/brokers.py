import logging
from instruments import Instrument
from orders import Order, Status, Side, Type, InvalidOrderCancelException


class ID_manager:
    def __init__(self):
        self.__id_dict = {}  # key: id(int), value: Ture

    # インスタンス単位でユニークな ID を生成します
    def generate_unique_id(self):
        if not self.__id_dict:
            self.__id_dict[0] = True
        uid = max(list(self.__id_dict.keys())) + 1
        self.__id_dict[uid] = True
        return uid


class Broker:
    def __init__(self):
        self.__current_candle = None
        self.__orders = {}  # key: id(int), value: order(order)
        self.__order_id_manager = ID_manager()
        self.__spread_calculator = SpreadsCalculator()

    def set_current_candle(self, candle):
        self.__current_candle = candle

    def register_order(self, order: Order):
        order_id = self.__order_id_manager.generate_unique_id()
        order.id = order_id
        self.__orders[order.id] = order

    def cancel_order(self, order: Order):
        candle = self.__current_candle
        if self.__orders in order.id:
            try:
                order.cancel(candle.date_time)
            except InvalidOrderCancelException as err:
                logging.warning("failed to cancel order: {}".format(err))
                return
            self.__orders.pop(order.id)

    def get_pending_orders(self):
        pending_orders = []
        for o in self.__orders:
            if o.get_status is Status.PENDING:
                pending_orders.append(o)
        return pending_orders

    def get_entered_orders(self):
        entered_orders = []
        for o in self.__orders:
            if o.get_status is Status.ENTERED:
                entered_orders.append(o)
        return entered_orders

    def on_candles(self, recorder):
        self.__process_orders()
        # TODO: レコーディング処理

    def __process_orders(self):
        candle = self.__current_candle
        for order in self.__orders:
            enter_execution_price = self.__spread_calculator.calculate_enter_execution_price(order)
            stop_execution_price = self.__spread_calculator.calculate_stop_execution_price(order)
            limit_execution_price = self.__spread_calculator.calculate_limit_execution_price(order)

            # enter
            if order.status is Status.PENDING and candle.is_include(enter_execution_price):
                order.status = Status.ENTERED
                order.entered_datetime = candle.date_time
                order.executed_enter_price = enter_execution_price

            # stop
            if order.status is Status.ENTERED and candle.is_include(stop_execution_price):
                order.status = Status.EXITED
                order.closed_datetime = candle.date_time
                order.executed_exited_price = stop_execution_price
                order.exited_order_type = Type.MARKET_IF_TOUCHED

            # limit
            if order.status is Status.ENTERED and candle.is_include(limit_execution_price):
                order.status = Status.EXITED
                order.closed_datetime = candle.date_time
                order.executed_exited_price = limit_execution_price
                order.exited_order_type = Type.MARKET_IF_TOUCHED


class SpreadsCalculator:
    __table = {
        Instrument.USD_JPY: 0.8,
        Instrument.EUR_JPY: 1.5,
        Instrument.AUD_JPY: 1.6,
        Instrument.GBP_JPY: 3.6,
        Instrument.EUR_USD: 0.8,
        Instrument.GBP_USD: 1.3,
        Instrument.AUD_USD: 1.4,
        Instrument.NZD_USD: 1.7,
        Instrument.EUR_GBP: 1.5
    }

    def get_spread(self, instrument: Instrument):
        return self.__table[instrument]

    def calculate_enter_execution_price(self, order):
        return self.__calculate_order_execution_price(order.side, order.price, order.instrument)

    def calculate_stop_execution_price(self, order):
        side = None
        if order.side == Side.SELL:
            side = Side.BUY
        if order.side == Side.BUY:
            side = Side.SELL
        return self.__calculate_order_execution_price(side, order.stop_price, order.instrument)

    def calculate_limit_execution_price(self, order):
        side = None
        if order.side == Side.SELL:
            side = Side.BUY
        if order.side == Side.BUY:
            side = Side.SELL
        return self.__calculate_order_execution_price(side, order.limit_price, order.instrument)

    def __calculate_order_execution_price(self, side: Side, target_price: float, instrument: Instrument):
        half_spread = self.__table[instrument]
        if side is Side.SELL:
            return target_price + half_spread
        if side is Side.BUY:
            return target_price - half_spread
        return 0
