import time
import json

from csv import reader
from oanda import fx_lib
from backtester.cerebro import Cerebro
from backtester.strategies import Strategy
from backtester.brokers import Broker
from backtester.instruments import Instrument, pips_to_price
from backtester.orders import Order, Side, Type, Status
from backtester.optimizer import Optimizer


class OrderManager():
    def __init__(self, order: Order, determined_price):
        self.order = order
        self.determined_price = determined_price  # エントリーの決手となった position book の価格


class NU4EOrder(Order):
    def __init__(self, instrument: Instrument,
                 side: Side,
                 order_type: Type,
                 unit: int,
                 price: float,
                 limit_price: float,
                 stop_price: float,
                 determined_price: float
                 ):
        super().__init__(instrument, side, order_type, unit, price, limit_price, stop_price)
        self.determined_price = determined_price
        self.exit_count_percent = 0

    def should_close(self, current_position_book):
        percent = ""
        if self.side is Side.BUY:
            percent = "longCountPercent"
        if self.side is Side.SELL:
            percent = "shortCountPercent"
        buckets = {}
        for pb in current_position_book:
            if pb["price"] == self.determined_price:
                buckets = pb
        if self.status is Status.ENTERED:
            if buckets[percent] <= self.exit_count_percent:
                return True
        return False

    def calculate_exit_position_count_percent(self, before_position_book: list, current_position_book: list,
                                              exit_threshold: float):
        percent = ""
        if self.side is Side.BUY:
            percent = "longCountPercent"
        if self.side is Side.SELL:
            percent = "shortCountPercent"
        now = 0
        for pb in current_position_book:
            if pb["price"] == self.determined_price:
                now = pb[percent]
        before = 0
        for pb in before_position_book:
            if pb["price"] == self.determined_price:
                before = pb[percent]
        self.exit_count_percent = now - (now - before) * exit_threshold


class NU4EStrategy(Strategy):
    def __init__(self, instrument: Instrument, params: dict, order_books: dict, position_books: dict):
        super().__init__(instrument, params, order_books, position_books)
        self.sliding_minutes = 1
        self.__entered_orders = {}  # {id: order}

    def on_candle(self, broker: Broker):
        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.close_all_entered_orders(broker)
            self.cancel_all_pending_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():

            # 買い
            if self.should_buy_entry() and len(broker.get_entered_orders()) == 0:
                stop_price = self.current_price() - pips_to_price(self.instrument, self.params["stopLossDistance"])
                decisive_price = self.__search_decisive_price(Side.BUY)
                new_buy_order = NU4EOrder(self.instrument, Side.BUY, Type.MARKET, 1, None, None, stop_price,
                                          decisive_price)
                new_buy_order.calculate_exit_position_count_percent(
                    self.before_position_book(),
                    self.current_position_book(),
                    self.params["exit_threshold"]
                )
                self.enter_order(new_buy_order, broker)

            # 売り
            if self.should_sell_entry() and len(broker.get_entered_orders()) == 0:
                stop_price = self.current_price() + pips_to_price(self.instrument, self.params["stopLossDistance"])
                decisive_price = self.__search_decisive_price(Side.SELL)
                new_sell_order = NU4EOrder(self.instrument, Side.SELL, Type.MARKET, 1, None, None, stop_price,
                                           decisive_price)
                new_sell_order.calculate_exit_position_count_percent(
                    self.before_position_book(),
                    self.current_position_book(),
                    self.params["exit_threshold"]
                )
                self.enter_order(new_sell_order, broker)

            # 決済
            for entered_order in list(self.__entered_orders.values()):
                if self.current_position_book_is_exist():
                    if entered_order.should_close(self.current_position_book()):
                        self.exit_order(entered_order, broker)
                else:
                    self.exit_order(entered_order, broker)

    def exit_order(self, order: Order, broker: Broker):
        broker.market_exit_order(order)
        self.__entered_orders.pop(order.id)

    def enter_order(self, order: Order, broker: Broker):
        broker.market_enter_order(order)
        self.__entered_orders[order.id] = order

    def should_buy_entry(self):
        if not self.current_position_book_is_exist() or not self.before_position_book_is_exist():
            return False
        if self.calculate_slope_of_trend() <= self.params["min_slope_of_trend"]:
            return False
        return self.__search_decisive_price(Side.BUY) is not None

    def should_sell_entry(self):
        if not self.current_position_book_is_exist() or not self.before_position_book_is_exist():
            return False
        if self.calculate_slope_of_trend() <= self.params["min_slope_of_trend"]:
            return False
        return self.__search_decisive_price(Side.SELL) is not None

    def __search_decisive_price(self, side: Side):
        percent = ""
        if side is Side.BUY:
            percent = "longCountPercent"
        if side is Side.SELL:
            percent = "shortCountPercent"
        if not self.current_position_book_is_exist() or not self.before_position_book_is_exist():
            return None
        now_p_buckets = fx_lib.divide_buckets_up_and_down(self.current_position_book(), self.current_price())
        before_p_buckets = fx_lib.divide_buckets_up_and_down(self.before_position_book(), self.current_price())
        for i in range(self.params["target_range"]):
            # low
            now = now_p_buckets["low"][i][percent]
            before = before_p_buckets["low"][i][percent]
            position_growth_rate = self.calculate_position_growth_rate(now, before)
            if position_growth_rate >= self.params["entry_threshold"] \
                    and before > self.params["min_required_count_percent"]:
                return now_p_buckets["low"][i]["price"]
            # high
            now = now_p_buckets["high"][i][percent]
            before = before_p_buckets["high"][i][percent]
            position_growth_rate = self.calculate_position_growth_rate(now, before)
            if position_growth_rate >= self.params["entry_threshold"] \
                    and before > self.params["min_required_count_percent"]:
                return now_p_buckets["low"][i]["price"]
        return None

    @staticmethod
    def calculate_position_growth_rate(now: float, before: float):
        if before == 0:
            return 0
        return (now - before) / before

    def calculate_slope_of_trend(self):
        buckets = fx_lib.divide_buckets_up_and_down(self.before_position_book(), self.current_price())
        low = buckets["low"]
        high = buckets["high"]
        short_sum = 0
        long_sum = 0
        for i in range(self.params["target_range"]):
            short_sum += low[i]["shortCountPercent"] + high[i]["shortCountPercent"]
            long_sum += low[i]["longCountPercent"] + high[i]["longCountPercent"]
        return (long_sum - short_sum) / (long_sum + short_sum)

if __name__ == "__main__":
    # read position books from json file.
    position_books_json = open("../data/position_book/NZD_USD_OB_2020-01-01_2021-01-01.json")
    position_books = json.load(position_books_json)
    # read candles from csv file.
    with open("../data/candles/NZD_USD_1T_2020-01-01_2021-01-01.csv", "r") as read_obj:
        feed = Cerebro.convert_feed_to_candles(list(reader(read_obj)))

    instrument = Instrument.NZD_USD

    # back_test
    params = {
        "entry_threshold": 0.58,  # entry 条件
        "exit_threshold": 0.7,  # exit 条件
        "min_slope_of_trend": -0.23,
        "min_required_count_percent": 0.05,
        "stopLossDistance": 10,  # 損切り幅(pips)
        "target_range": 2,  # position book を確認する価格帯の範囲
    }
    my_strategy = NU4EStrategy(instrument, params, None, position_books)
    start = time.time()
    print("Start back test.")
    cerebro = Cerebro(feed, my_strategy, 0, True)
    cerebro.result_dir_name = "NU4E_beta2_2020-2021"
    cerebro.run()
    print("Execution time: {}".format(time.time() - start))
    cerebro.recorder.print_result()
    cerebro.recorder.plot()

    # optimize
    # param_ranges = {
    #     "entry_threshold": {"min": 0.58, "max": 0.6, "step": 0.1},
    #     "exit_threshold": {"min": 0.7, "max": 0.71, "step": 0.1},
    #     "min_slope_of_trend": {"min": -0.5, "max": 1.0, "step": 0.01},
    #     "min_required_count_percent": {"min": 0.15, "max": 0.16, "step": 0.1},
    #     "stopLossDistance": {"min": 10, "max": 11, "step": 1},
    #     "target_range": {"min": 2, "max": 3, "step": 1},
    # }
    # optimizer = Optimizer(feed, NU4EStrategy, instrument, param_ranges, None, position_books)
    # print("Start optimize.")
    # start = time.time()
    # optimizer.result_dir_name = "NU4E_beta2_2020-2021"
    # optimizer.optimize()
    # print("Execution time: {}".format(time.time() - start))
