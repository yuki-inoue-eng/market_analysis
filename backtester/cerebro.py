import time
import pandas as pd
import logging
from orders import Order, Status, InvalidOrderCancelException


class Cerebro:
    def __init__(self, feed: pd.DataFrame, strategy):
        self.__feed = feed
        self.__strategy = strategy
        self.__recorder = Recorder()
        self.__broker = Broker()

    def run(self):
        pass


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
        self.__current_bar = None
        self.__orders = {}  # key: id(int), value: order(order)
        self.__order_id_manager = ID_manager()

    def set_current_bar(self, bar):
        self.__current_bar = bar

    def register_order(self, order: Order):
        order_id = self.__order_id_manager.generate_unique_id()
        order.id = order_id
        self.__orders[order.id] = order

    def cancel_order(self, order: Order):
        if self.__orders in order.id:
            try:
                order.cancel(self.__current_bar.date_time)  # TODO: date_time を正しく引数に渡す
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

    def on_bars(self, recorder):
        pass


class Recorder:
    def __init__(self):
        pass

# if __name__ == '__main__':
#     pass
