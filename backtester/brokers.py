import logging
from instruments import Instrument
from orders import Order, Status, Side, ExitedType, InvalidOrderCancelException


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

    def exit_order(self, order: Order):
        if self.__orders in order.id:
            current_date_time = self.__current_candle.date_time
            target_exit_price = self.__current_candle.close
            execution_price = self.__spread_calculator.calculate_market_exit_execution_price(order, target_exit_price)
            order.status = Status.EXITED
            order.exited_datetime = current_date_time
            order.exited_price = target_exit_price
            order.executed_enter_price = execution_price
            order.exited_type = ExitedType.MARKET
            self.__orders.pop(order.id)

    def cancel_order(self, order: Order):
        # TODO order キャンセルの処理を全てこちらへ移行する
        if self.__orders in order.id and order.status is Status.PENDING:
            current_date_time = self.__current_candle.date_time
            try:
                order.cancel(current_date_time)
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
                order.entered_price = order.price
                order.executed_enter_price = enter_execution_price

            # stop
            if order.status is Status.ENTERED and candle.is_include(stop_execution_price):
                order.status = Status.EXITED
                order.closed_datetime = candle.date_time
                order.exited_price = order.stop_price
                order.executed_exited_price = stop_execution_price
                order.exited_type = ExitedType.STOP
                self.__orders.pop(order.id)

            # limit
            if order.status is Status.ENTERED and candle.is_include(limit_execution_price):
                order.status = Status.EXITED
                order.closed_datetime = candle.date_time
                order.exited_price = order.limit_price
                order.executed_exited_price = limit_execution_price
                order.exited_type = ExitedType.LIMIT
                self.__orders.pop(order.id)


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

    def calculate_enter_execution_price(self, order: Order):
        return self.__calculate_order_execution_price(order.side, order.price, order.instrument)

    def calculate_stop_execution_price(self, order: Order):
        side = None
        if order.side == Side.SELL:
            side = Side.BUY
        if order.side == Side.BUY:
            side = Side.SELL
        return self.__calculate_order_execution_price(side, order.stop_price, order.instrument)

    def calculate_limit_execution_price(self, order: Order):
        side = None
        if order.side == Side.SELL:
            side = Side.BUY
        if order.side == Side.BUY:
            side = Side.SELL
        return self.__calculate_order_execution_price(side, order.limit_price, order.instrument)

    def calculate_market_exit_execution_price(self, order: Order, price: float):
        side = None
        if order.side == Side.SELL:
            side = Side.BUY
        if order.side == Side.BUY:
            side = Side.SELL
        return self.__calculate_order_execution_price(side, price, order.instrument)

    def __calculate_order_execution_price(self, side: Side, target_price: float, instrument: Instrument):
        half_spread = self.__table[instrument]
        if side is Side.SELL:
            return target_price + half_spread
        if side is Side.BUY:
            return target_price - half_spread
        return 0
