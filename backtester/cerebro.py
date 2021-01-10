import time
import pandas as pd
from orders import Order, Status



class Cerebro:
    def __init__(self, feed: pd.DataFrame, strategy):
        self.__feed = feed
        self.__strategy = strategy
        self.__recorder = Recorder()
        self.__broker = Broker()

    def run(self):
        # some heavy processing
        time.sleep(3)


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
        order.set_order_id(order_id)
        self.__orders[order.get_order_id()] = order

    def cancel_order(self, order: Order):
        order.set_status(Status.CANCELED)
        if self.__orders in order.get_order_id():
            self.__orders.pop(order.get_order_id())
        return

    def onBars(self, recorder):
        pass





class Recorder:
    def __init__(self):
        pass

# if __name__ == '__main__':
#     pass
