# ロジックの説明文を追加

import time
import json
from datetime import datetime, timezone
from csv import reader
from oanda import fx_lib
from backtester.cerebro import Cerebro
from backtester.strategies import Strategy
from backtester.brokers import Broker
from backtester.instruments import Instrument, pips_to_price
from backtester.orders import Order, Side, Type
from backtester.optimizer import Optimizer


class OB1Strategy(Strategy):
    def __init__(self, instrument: Instrument, params: dict, order_books: dict, position_books: dict):
        super().__init__(instrument, params, order_books, position_books)
        self.sliding_minutes = 1
        self.__entered_orders = {}  # {id: order}

    def on_candle(self, broker: Broker):
        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.close_all_entered_orders(broker)
            self.cancel_all_pending_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():

            # 決済
            for entered_order in list(self.__entered_orders.values()):
                if entered_order.side is Side.BUY and (not self.should_continue_buy() or self.should_sell_entry()):
                    self.exit_order(entered_order, broker)
                if entered_order.side is Side.SELL and (not self.should_continue_sell() or self.should_buy_entry()):
                    self.exit_order(entered_order, broker)

            # 買い
            if self.should_buy_entry() and len(broker.get_entered_orders()) == 0:
                stop_price = self.current_price() - pips_to_price(self.instrument, self.params["stop_loss_distance"])
                limit_price = self.current_price() + pips_to_price(self.instrument, self.params["limit_distance"])
                new_buy_order = Order(self.instrument, Side.BUY, Type.MARKET, 1, None, limit_price, stop_price)
                self.enter_order(new_buy_order, broker)

            # 売り
            if self.should_sell_entry() and len(broker.get_entered_orders()) == 0:
                stop_price = self.current_price() + pips_to_price(self.instrument, self.params["stop_loss_distance"])
                limit_price = self.current_price() - pips_to_price(self.instrument, self.params["limit_distance"])
                new_sell_order = Order(self.instrument, Side.SELL, Type.MARKET, 1, None, limit_price, stop_price)
                self.enter_order(new_sell_order, broker)

    def exit_order(self, order: Order, broker: Broker):
        broker.market_exit_order(order)
        self.__entered_orders.pop(order.id)

    def enter_order(self, order: Order, broker: Broker):
        broker.market_enter_order(order)
        self.__entered_orders[order.id] = order

    def should_continue_buy(self):
        return self.should_buy_entry()

    def should_continue_sell(self):
        return self.should_sell_entry()

    def should_buy_entry(self):
        if not self.current_order_book_is_exist() or not self.current_position_book_is_exist():
            return False
        if self.high_volatility_ob():
            return False
        if not self.buy_advantage():
            return False
        if self.sum_sell_power() == 0 or self.sum_sell_fuel() == 0:
            return False
        return self.sum_buy_power() / self.sum_sell_power() > params["power_threshold"] \
               and self.sum_buy_fuel() / self.sum_sell_fuel() > params["fuel_threshold"]

    def should_sell_entry(self):
        if not self.current_order_book_is_exist() or not self.current_position_book_is_exist():
            return False
        if self.high_volatility_ob():
            return False
        if not self.sell_advantage():
            return False
        if self.sum_buy_power() == 0 or self.sum_buy_fuel() == 0:
            return False
        return self.sum_sell_power() / self.sum_buy_power() > params["power_threshold"] \
           and self.sum_sell_fuel() / self.sum_buy_fuel() > params["fuel_threshold"]

    def buy_advantage(self):
        return self.sum_buy_power() > self.sum_sell_power() and self.sum_buy_fuel() > self.sum_sell_fuel()

    def sell_advantage(self):
        return self.sum_sell_power() > self.sum_buy_power() and self.sum_sell_fuel() > self.sum_buy_fuel()

    def sum_buy_power(self):
        if self.high_volatility_ob():
            return 0
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_order_book()["buckets"], self.current_price())
        sum_long = 0
        for i in range(self.params["power_count_range"]):
            sum_long += now_buckets["high"][i]["longCountPercent"]  # / (i+1)
        return sum_long

    def sum_sell_power(self):
        if self.high_volatility_ob():
            return 0
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_order_book()["buckets"], self.current_price())
        sum_short = 0
        for i in range(self.params["power_count_range"]):
            sum_short += now_buckets["low"][i]["shortCountPercent"]  # / (i+1)
        return sum_short

    def sum_buy_fuel(self):
        if self.high_volatility_pb():
            return 0
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_position_book()["buckets"], self.current_price())
        sum_short = 0
        invalid_range = 2
        for i in range(invalid_range, self.params["power_count_range"]):
            sum_short += now_buckets["low"][i]["shortCountPercent"]  # / (i+1)
        return sum_short

    def sum_sell_fuel(self):
        if self.high_volatility_pb():
            return 0
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_position_book()["buckets"], self.current_price())
        sum_long = 0
        invalid_range = 2
        for i in range(invalid_range, self.params["power_count_range"]):
            sum_long += now_buckets["high"][i]["longCountPercent"]  # / (i+1)
        return sum_long

    def high_volatility_ob(self):
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_order_book()["buckets"], self.current_price())
        if len(now_buckets["low"]) < 5 or len(now_buckets["high"]) < 5:
            return True
        low_distance = abs(self.current_price() - now_buckets["low"][0]["price"])
        high_distance = abs(self.current_price() - now_buckets["high"][0]["price"])
        return low_distance + high_distance > pips_to_price(self.instrument, 5)

    def high_volatility_pb(self):
        now_buckets = fx_lib.divide_buckets_up_and_down(self.current_position_book()["buckets"], self.current_price())
        if len(now_buckets["low"]) < 5 or len(now_buckets["high"]) < 5:
            return True
        low_distance = abs(self.current_price() - now_buckets["low"][0]["price"])
        high_distance = abs(self.current_price() - now_buckets["high"][0]["price"])
        return low_distance + high_distance > pips_to_price(self.instrument, 5)


if __name__ == "__main__":
    instrument = Instrument.USD_JPY
    d_from = "2018-01-01"
    d_to = "2019-01-01"

    d_from_year = int(d_from.split("-")[0])
    d_from_month = int(d_from.split("-")[1])
    d_from_date = int(d_from.split("-")[2])
    date_from = datetime(d_from_year, d_from_month, d_from_date, 0, 0, tzinfo=timezone.utc)
    d_to_year = int(d_to.split("-")[0])
    d_to_month = int(d_to.split("-")[1])
    d_to_date = int(d_to.split("-")[2])
    date_to = datetime(d_to_year, d_to_month, d_to_date, 0, 0, tzinfo=timezone.utc)

    # read books from json file.
    order_books_json = open("../data/order_book/USD_JPY_OB_2018-01-01_2019-01-01.json")
    order_books = json.load(order_books_json)
    position_books_json = open("../data/position_book/USD_JPY_PB_2018-01-01_2019-01-01.json")
    position_books = json.load(position_books_json)
    # read candles from csv file.
    with open("../data/candles/USD_JPY_1T_2018-01-01_2019-01-01.csv", "r") as read_obj:
        feed = Cerebro.convert_feed_to_candles(list(reader(read_obj)), date_from, date_to)

    params = {
        "power_threshold": 2.0,  # entry 条件
        "fuel_threshold": 1.9,
        "power_count_range": 5,  # position book を確認する価格帯の範囲
        "fuel_count_range": 5,
        "stop_loss_distance": 15,
        "limit_distance": 200
    }
    # back_test
    my_strategy = OB1Strategy(instrument, params, order_books, position_books)
    start = time.time()
    print("Start back test.")
    cerebro = Cerebro(feed, my_strategy, 0, True)
    cerebro.result_dir_name = "OB1_{}-{}_BUY_ONLY".format(d_from, d_to)
    cerebro.run()
    print("Execution time: {}".format(time.time() - start))
    cerebro.recorder.print_result()
    cerebro.recorder.plot()

    # optimize
    # param_ranges = {
    #     "entry_threshold": {"min": 0.58, "max": 0.59, "step": 0.1},
    #     "exit_threshold": {"min": 0.0, "max": 1.6, "step": 0.01},
    #     "buy_growth_rate_weight": {"min": 3.35, "max": 3.36, "step": 0.1},
    #     "min_slope_of_trend": {"min": -0.23, "max": -0.22, "step": 0.1},
    #     "min_required_count_percent": {"min": 0.15, "max": 0.16, "step": 0.1},
    #     "stopLossDistance": {"min": 10, "max": 11, "step": 1},
    #     "target_range": {"min": 2, "max": 3, "step": 1},
    # }
    # optimizer = Optimizer(feed, OB1Strategy, instrument, param_ranges, order_books, position_books)
    # print("Start optimize.")
    # start = time.time()
    # optimizer.result_dir_name = "OB1_{}-{}_entry_threshold".format(d_from, d_to)
    # optimizer.optimize()
    # print("Execution time: {}".format(time.time() - start))
