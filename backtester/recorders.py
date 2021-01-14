from orders import Order, Status, Side
from instruments import pips_to_price, price_to_pips


class Recorder:
    def __init__(self):
        self.orders = {}  # key: id(int), value: order(order)
        self.total_profit_pips = None
        self.total_number_of_trades = self.total_number_of_trades()
        self.win_rate = 0

    def record(self, order: Order):
        self.orders[order.id] = order

    def aggregate(self):
        self.remove_canceled_order_record()
        self.total_profit_pips = self.sum_profit_margin_pips()
        self.total_number_of_trades = self.total_number_of_trades()
        self.win_rate = self.win_rate()

    def sum_profit_margin(self):
        sum_p = 0
        for order in self.orders:
            sum_p += self.profit_margin(order)
        return sum_p

    def sum_profit_margin_pips(self):
        sum_pips = 0
        for order in self.orders:
            sum_pips += self.profit_margin_pips(order)
        return sum_pips

    def profit_margin_pips(self, order: Order):
        return price_to_pips(order.instrument, self.profit_margin(order))

    def total_number_of_trades(self):
        n = 0
        for order in self.orders:
            if order.status is Status.EXITED:
                n += 1
        return n

    def calc_win_rate(self):
        orders = []
        sum_win = 0
        for order in self.orders:
            if order.status is Status.EXITED:
                orders.append(order)
        for order in orders:
            if self.profit_margin(order) > 0:
                sum_win += 1
        return sum_win / len(orders)

    def remove_canceled_order_record(self):
        for order in self.orders:
            if order.status is not Status.EXITED:
                self.orders.pop(order.id)

    @staticmethod
    def profit_margin(order: Order):
        if order.side == Side.SELL:
            return order.entered_price - order.exited_price
        elif order.side == Side.BUY:
            return order.exited_price - order.entered_price
        return 0
