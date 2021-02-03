from .orders import Order, Status, Side, ExitedType
from .instruments import price_to_pips
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd


class Recorder:
    def __init__(self):
        self.orders = {}  # key: id(int), value: order(order)
        self.total_pips = self.__sum_profit_margin_pips()
        self.total_number_of_touched_stop = self.__total_number_of_touched_stop()
        self.total_number_of_touched_limit = self.__total_number_of_touched_limit()
        self.total_number_of_trades = self.__total_number_of_trades()
        self.touched_stop_rate = 0

    def record(self, order: Order):
        self.orders[order.id] = order

    def aggregate(self):
        self.__remove_canceled_order_record()
        self.total_pips = self.__sum_profit_margin_pips()
        self.total_number_of_touched_stop = self.__total_number_of_touched_stop()
        self.total_number_of_trades = self.__total_number_of_trades()
        self.touched_stop_rate = self.__calc_touched_stop_rate()

    def result_pips_data_frame(self):
        columns = ["datetime", "pips"]
        dataset = []
        for order in self.orders.values():
            pips = self.__profit_margin_pips(order)
            dataset.append([order.entered_datetime, 0])
            dataset.append([order.closed_datetime, pips])
        df = pd.DataFrame(dataset, columns=columns)
        df = df.sort_values(by="datetime")  # ソート
        df = df.assign(cumsum_pips=df["pips"].cumsum())  # 累積和の列を追加
        return df

    def make_graph(self):
        df = self.result_pips_data_frame()
        plt.figure(figsize=(16, 8))
        plt.plot(df['datetime'], df["cumsum_pips"])

        # ロケータで刻み幅を設定
        xloc = mpl.dates.MonthLocator()
        plt.gca().xaxis.set_major_locator(xloc)

        # 時刻のフォーマットを設定
        xfmt = mpl.dates.DateFormatter("%Y/%m")
        plt.gca().xaxis.set_major_formatter(xfmt)

        return plt

    def plot(self):
        self.make_graph().show()

    def print_result(self):
        print("Total number of trades: {}".format(self.total_number_of_trades))
        print("Total total_profit_pips: {} pips".format(self.total_pips))

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

    def __total_number_of_touched_stop(self):
        n = 0
        for order in self.orders.values():
            if order.exited_type is ExitedType.STOP:
                n += 1
        return n

    def __total_number_of_touched_limit(self):
        n = 0
        for order in self.orders.values():
            if order.exited_type is ExitedType.LIMIT:
                n += 1
        return n

    def __calc_touched_stop_rate(self):
        if self.total_number_of_trades == 0:
            return 0
        return self.total_number_of_touched_stop / self.total_number_of_trades

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
