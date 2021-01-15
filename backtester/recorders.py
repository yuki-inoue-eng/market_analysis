from .orders import Order, Status, Side
from .instruments import price_to_pips


class Recorder:
    def __init__(self):
        self.orders = {}  # key: id(int), value: order(order)
        self.total_profit_pips = None
        self.total_number_of_trades = self.__total_number_of_trades()
        self.win_rate = 0

    def record(self, order: Order):
        self.orders[order.id] = order

    def aggregate(self):
        self.__remove_canceled_order_record()
        self.total_profit_pips = self.__sum_profit_margin_pips()
        self.total_number_of_trades = self.__total_number_of_trades()
        self.win_rate = self.__calc_win_rate()

    def __sum_profit_margin(self):
        sum_p = 0
        for order in self.orders.values():
            sum_p += self.__profit_margin(order)
        return sum_p

    def __sum_profit_margin_pips(self):
        sum_pips = 0
        for order in self.orders.values():
            sum_pips += self.__profit_margin_pips(order)
        return sum_pips

    def __profit_margin_pips(self, order: Order):
        return price_to_pips(order.instrument, self.__profit_margin(order))

    def __total_number_of_trades(self):
        n = 0
        for order in self.orders.values():
            if order.status is Status.EXITED:
                n += 1
        return n

    def __calc_win_rate(self):
        orders = []
        sum_win = 0
        for order in self.orders.values():
            if order.status is Status.EXITED:
                orders.append(order)
        for order in orders:
            if self.__profit_margin(order) > 0:
                sum_win += 1
        return sum_win / len(orders)

    def __remove_canceled_order_record(self):
        for order in list(self.orders.values()):
            if order.status is not Status.EXITED:
                self.orders.pop(order.id)

    @staticmethod
    def __profit_margin(order: Order):
        if order.side == Side.SELL:
            return order.entered_price - order.exited_price
        elif order.side == Side.BUY:
            return order.exited_price - order.entered_price
        return 0
