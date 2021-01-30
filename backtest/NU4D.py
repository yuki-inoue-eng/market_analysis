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


# 成り行き注文ロジック
class NU4DStrategy(Strategy):
    def __init__(self, order_books: dict, position_books: dict, params: dict):
        super().__init__(params)
        self.__order_books = order_books
        self.__position_books = position_books
        self.__sliding_minutes = 1
        self.__instrument = Instrument.NZD_USD
        self.__entered_orders = {}

        if self.params["relativize"]:
            self.__relativize_book(self.__order_books)
            self.__relativize_book(self.__position_books)

    # 引数に指定した books の値を相対的なものに変換します。
    @staticmethod
    def __relativize_book(books: dict):
        for buckets in books.values():
            short_sum = sum([bucket["shortCountPercent"] for bucket in buckets])
            long_sum = sum([bucket["longCountPercent"] for bucket in buckets])
            buckets_sum = short_sum + long_sum
            for bucket in buckets:
                bucket["shortCountPercent"] *= buckets_sum
                bucket["longCountPercent"] *= buckets_sum

    def on_candle(self, broker: Broker):
        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.close_all_entered_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():
            current_price = self.current_candle.close
            current_book_time_stamp_str = str(math.floor(self.get_current_book_time_stamp()))
            before_book_time_stamp_str = str(math.floor(self.get_before_book_time_stamp()))

            # order book と position book のデータが存在し、ポジションを保持していない場合は新規注文処理を実行
            if self.book_is_exist(self.__order_books, current_book_time_stamp_str) \
                    and self.book_is_exist(self.__order_books, before_book_time_stamp_str) \
                    and self.book_is_exist(self.__position_books, current_book_time_stamp_str) \
                    and len(broker.get_entered_orders()) == 0:
                new_order = self.__create_new_orders_logic_type_d(
                    self.__instrument,
                    self.params,
                    self.__position_books[current_book_time_stamp_str],
                    self.__order_books[current_book_time_stamp_str],
                    self.__order_books[before_book_time_stamp_str],
                    current_price,
                    self.params["target_range"]
                )
                if new_order is not None:
                    broker.market_enter_order(new_order)
                    self.__entered_orders[new_order.id] = True

            # エントリー中の注文がある場合に決済すべきか検査します。position book が存在しない場合は、強制的に決済します。
            if self.book_is_exist(self.__position_books, current_book_time_stamp_str):
            # if current_book_time_stamp_str in self.__position_books:
                for order in broker.get_entered_orders():
                    if self.__order_should_close_logic_type_d(
                            order,
                            self.params,
                            self.__position_books[current_book_time_stamp_str],
                            current_price,
                            self.params["target_range"]
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

    # current_price には ローソク足の終値を入れます。
    def __create_new_orders_logic_type_d(self, instrument: Instrument, params: dict, current_p_buckets: list,
                                         current_o_buckets: list, before_o_buckets: list, current_price: float,
                                         target_range: int):
        current_p_buckets = fx_lib.divide_buckets_up_and_down(current_p_buckets, current_price)
        current_o_buckets = fx_lib.divide_buckets_up_and_down(current_o_buckets, current_price)
        before_o_buckets = fx_lib.divide_buckets_up_and_down(before_o_buckets, current_price)
        current_p_low = current_p_buckets["short"]
        current_p_high = current_p_buckets["long"]
        current_o_short = current_o_buckets["short"]
        before_o_short = before_o_buckets["short"]
        if self.__o_short_is_over(current_o_short, params["nowStopOrder"], target_range) \
                and not self.__o_short_is_over(before_o_short, params["beforeStopOrder"], target_range) \
                and self.__p_bucket_is_over(current_p_low, current_p_high, params["nowBuyPosition"], 3):
            stop_price = current_price - pips_to_price(instrument, params["stopLossDistance"])
            return Order(instrument, Side.BUY, Type.MARKET, 1, None, None, stop_price)

    # エントリー中のオーダーを決済すべきか判断します。
    def __order_should_close_logic_type_d(self, order: Order, params: dict, current_p_buckets: list,
                                          current_price: float, target_range: int):
        current_p_buckets = fx_lib.divide_buckets_up_and_down(current_p_buckets, current_price)
        current_p_low = current_p_buckets["short"]
        current_p_high = current_p_buckets["long"]
        if order.status is Status.ENTERED \
                and not self.__p_bucket_is_over(current_p_low, current_p_high, params["nowBuyPosition"],
                                                params["target_range"]):
            return True
        return False

    # target_range で指定した数分の position book bucket を検査し、閾値を超える買いポジションのある価格帯が存在している場合は True 、ない場合は False を返します。
    # p_low: 現在価格より下の position book buckets
    # p_high: 現在価格より上の position book buckets
    # threshold: 閾値
    # target_range: チェックする buckets 範囲
    @staticmethod
    def __p_bucket_is_over(p_low: list, p_high: list, threshold: float, target_range: int):
        for i in range(target_range):
            if p_low[i]["longCountPercent"] > threshold:
                return True
            if p_high[i]["longCountPercent"] > threshold:
                return True
        return False

    # target_range で指定した数分の order book bucket を検査し、閾値を超える売り注文のある価格帯が存在している場合は True 、ない場合は False を返します。
    # o_short: 現在価格より下の book buckets
    # threshold: 閾値
    # target_range: チェックする buckets 範囲
    @staticmethod
    def __o_short_is_over(o_short: list, threshold: float, target_range: int):
        for i in range(target_range):
            if o_short[i]["shortCountPercent"] > threshold:
                return True
        return False


if __name__ == "__main__":
    # read order books from json file.
    order_books_json = open("../data/order_book/NZD_USD_OB_2020-01-01_2021-01-01.json")
    # read position books from json file.
    position_books_json = open("../data/position_book/NZD_USD_OB_2020-01-01_2021-01-01.json")
    # read candles from csv file.
    with open("../data/candles/NZD_USD_1T_2020-01-01_2021-01-01.csv", "r") as read_obj:
        feed = Cerebro.convert_feed_to_candles(list(reader(read_obj)))

    order_books = json.load(order_books_json)
    position_books = json.load(position_books_json)

    # # back_test
    # params = {
    #     "nowBuyPosition": 8,  # 買いポジションの閾値
    #     "nowStopOrder": 7,  # 現在のストップ売りの閾値(下限)
    #     "beforeStopOrder": 8,  # 直近のストップ売りの閾値(上限)
    #     "stopLossDistance": 8,  # 損切り幅(pips)
    #     "target_range": 10,  # order book, position book を確認する価格帯の範囲
    #     "relativize": True,
    # }
    # my_strategy = NU4DStrategy(order_books, position_books, params)
    # start = time.time()
    # print("Start back test.")
    # cerebro = Cerebro(feed, my_strategy, 0)
    # cerebro.run()
    # print("Execution time: {}".format(time.time() - start))
    # cerebro.recorder.print_result()
    # cerebro.recorder.plot()

    # optimize
    param_ranges = {
        "nowBuyPosition": {"min": 6, "max": 10, "step": 1},
        "nowStopOrder": {"min": 6, "max": 10, "step": 1},
        "beforeStopOrder": {"min": 6, "max": 10, "step": 1},
        "stopLossDistance": {"min": 8, "max": 9, "step": 1},
        "target_range": {"min": 10, "max": 11, "step": 1},
        "relativize": True
    }
    optimizer = Optimizer(order_books, position_books, feed, param_ranges, NU4DStrategy)
    print("Start optimize.")
    start = time.time()
    optimizer.optimize()
    print("Execution time: {}".format(time.time() - start))
    optimizer.print_result()