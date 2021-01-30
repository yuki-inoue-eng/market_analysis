import time
import json
import math

from datetime import timedelta
from csv import reader
from oanda import fx_lib
from backtester.cerebro import Cerebro
from backtester.strategies import Strategy
from backtester.brokers import Broker
from backtester.instruments import Instrument, pips_to_price
from backtester.orders import Order, Side, Type, Status
from backtester.optimizer import Optimizer


class NU4EStrategy(Strategy):
    def __init__(self, order_books: dict, position_books: dict, params: dict):
        super().__init__(params)
        self.__position_books = position_books
        self.__sliding_minutes = 1
        self.__instrument = Instrument.NZD_USD
        self.__entered_orders = {}  # {id: order}
        self.__target_position_recorder = {}  # {"price": 100, "exit_count_percent": 1.3}

    def on_candle(self, broker: Broker):
        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.close_all_entered_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():
            current_price = self.current_candle.close
            current_book_time_stamp_str = str(math.floor(self.get_current_book_time_stamp()))
            before_book_time_stamp_str = str(math.floor(self.get_before_book_time_stamp()))

            # 前回と今回のポジションブックを見てエントリーを行う
            if self.book_is_exist(self.__position_books, current_book_time_stamp_str) \
                    and self.book_is_exist(self.__position_books, before_book_time_stamp_str) \
                    and len(broker.get_entered_orders()) == 0:
                new_order = self.__creat_new_orders_logic_type_e(
                    self.__instrument,
                    self.params,
                    self.__position_books[current_book_time_stamp_str],
                    self.__position_books[before_book_time_stamp_str],
                    current_price,
                )
                if new_order is not None:
                    broker.market_enter_order(new_order)
                    self.__entered_orders[new_order.id] = True

            # 既にエントリー済みのオーダーを閉じるべきか検査を行う
            if self.book_is_exist(self.__position_books, current_book_time_stamp_str):
                for order in broker.get_entered_orders():
                    if self.__order_should_close_logic_type_e(
                            order,
                            self.__position_books[current_book_time_stamp_str],
                    ):
                        broker.market_exit_order(order)
                        self.__entered_orders.pop(order.id)
            else:
                for order in broker.get_entered_orders():
                    broker.market_exit_order(order)
                    self.__entered_orders.pop(order.id)


    @staticmethod
    def book_is_exist(book: dict, timestamp_str: str):
        return timestamp_str in book and len(book[timestamp_str]) > 0

    def get_current_book_time_stamp(self):
        dt = self.current_candle.date_time - timedelta(minutes=self.__sliding_minutes)
        return dt.timestamp()

    def get_before_book_time_stamp(self):
        return self.get_current_book_time_stamp() - 1200

    def is_lambda_invoke_time(self):
        dt = self.current_candle.date_time - timedelta(minutes=self.__sliding_minutes)
        return fx_lib.is_order_book_update_time(dt)

    def is_restraint_time_zone(self):
        return self.current_candle.date_time.hour == 21 or self.current_candle.date_time.hour == 20

    @staticmethod
    def cancel_all_pending_orders(broker: Broker):
        for order in broker.get_pending_orders():
            broker.cancel_order(order)

    @staticmethod
    def close_all_entered_orders(broker: Broker):
        for order in broker.get_entered_orders():
            broker.market_exit_order(order)

    def __creat_new_orders_logic_type_e(self, instrument: Instrument, params: dict, now_p_buckets: list,
                                        before_p_buckets: list, current_price: float,):
        now_p_buckets = fx_lib.divide_buckets_up_and_down(now_p_buckets, current_price)
        now_low = now_p_buckets["long"]
        now_high = now_p_buckets["short"]
        before_p_buckets = fx_lib.divide_buckets_up_and_down(before_p_buckets, current_price)
        before_low = before_p_buckets["long"]
        before_high = before_p_buckets["short"]
        should_entry = False
        for i in range(params["target_range"]):
            now = now_low[i]["longCountPercent"]
            before = before_low[i]["longCountPercent"]
            position_growth_rate = self.calculate_position_growth_rate(now, before)
            if position_growth_rate >= params["entry_threshold"] and before > params["min_required_count_percent"]:
                should_entry = True
                exit_count_percent = self.calculate_exit_position_count_percent(
                    now, before, params["exit_threshold"])
                self.__target_position_recorder = {
                    "price": now_low[i]["price"],
                    "exit_count_percent": exit_count_percent
                }
                break
            now = now_high[i]["longCountPercent"]
            before = before_high[i]["longCountPercent"]
            position_growth_rate = self.calculate_position_growth_rate(now, before)
            if position_growth_rate >= params["entry_threshold"] and before > params["min_required_count_percent"]:
                should_entry = True
                exit_count_percent = self.calculate_exit_position_count_percent(
                    now, before, params["exit_threshold"])
                self.__target_position_recorder = {
                    "price": now_high[i]["price"],
                    "exit_count_percent": exit_count_percent
                }
                break

        if should_entry:
            stop_price = current_price - pips_to_price(instrument, params["stopLossDistance"])
            return Order(instrument, Side.BUY, Type.MARKET, 1, None, None, stop_price)

    def __order_should_close_logic_type_e(self, order: Order, p_buckets):
        buckets = {}
        for pb in p_buckets:
            if pb["price"] == self.__target_position_recorder["price"]:
                buckets = pb
        if order.side is Side.BUY and order.status is Status.ENTERED:
            if buckets["longCountPercent"] <= self.__target_position_recorder["exit_count_percent"]:
                self.__target_position_recorder = {}
                return True
        return False

    @staticmethod
    def calculate_position_growth_rate(now: float, before: float):
        if before == 0:
            return 0
        return (now - before) / before

    @staticmethod
    def calculate_exit_position_count_percent(now: float, before: float, exit_threshold: float):
        return now - (now - before) * exit_threshold


if __name__ == "__main__":
    # read position books from json file.
    position_books_json = open("../data/position_book/NZD_USD_OB_2019-01-01_2020-01-01.json")
    # read candles from csv file.
    with open("../data/candles/NZD_USD_1T_2019-01-01_2020-01-01.csv", "r") as read_obj:
        feed = Cerebro.convert_feed_to_candles(list(reader(read_obj)))
    position_books = json.load(position_books_json)

    # back_test
    params = {
        "entry_threshold": 0.58,  # entry 条件
        "exit_threshold": 0.7,  # exit 条件
        "min_required_count_percent": 0.15,
        "stopLossDistance": 10,  # 損切り幅(pips)
        "target_range": 2,  # position book を確認する価格帯の範囲
    }
    my_strategy = NU4EStrategy(None, position_books, params)
    start = time.time()
    print("Start back test.")
    cerebro = Cerebro(feed, my_strategy, 0, True)
    cerebro.result_dir_name = "NU4E"
    cerebro.run()
    print("Execution time: {}".format(time.time() - start))
    cerebro.recorder.print_result()
    cerebro.recorder.plot()

    # optimize
    # param_ranges = {
    #     "entry_threshold": {"min": 1.1, "max": 1.2, "step": 0.1},
    #     "exit_threshold": {"min": 0.7, "max": 0.71, "step": 0.1},
    #     "min_required_count_percent": {"min": 0.04, "max": 0.05, "step": 0.01},
    #     "stopLossDistance": {"min": 10, "max": 11, "step": 1},
    #     "target_range": {"min": 2, "max": 3, "step": 1},
    # }
    # optimizer = Optimizer(None, position_books, feed, param_ranges, NU4EStrategy)
    # print("Start optimize.")
    # start = time.time()
    # optimizer.result_dir_name = "NU4E"
    # optimizer.optimize()
    # print("Execution time: {}".format(time.time() - start))