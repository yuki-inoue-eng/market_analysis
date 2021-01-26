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
from backtester.orders import Order, Side, Type


class NU3BStrategy(Strategy):
    def __init__(self, order_books: dict, params: dict):
        super().__init__()
        self.__order_books = order_books
        self.__sliding_minutes = 5
        self.__instrument = Instrument.NZD_USD
        self.__params = self.__build_params(params)

    @staticmethod
    def __build_params(params: dict):
        params["stopOrders"] = []
        params["stopOrders"].append(params["stopOrders_1"])
        params["stopOrders"].append(params["stopOrders_2"])
        params["stopOrders"].append(params["stopOrders_3"])
        return params


    def on_candle(self, broker: Broker):
        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.cancel_all_pending_orders(broker)
            self.close_all_entered_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():
            self.cancel_all_pending_orders(broker)
            current_price = self.current_candle.open
            time_stamp_str = str(math.floor(self.get_current_order_book_time_stamp()))
            if not (time_stamp_str in self.__order_books):
                return
            if len(broker.get_entered_orders()) != 0:
                return
            buckets = self.__order_books[time_stamp_str]
            new_orders = self.create_new_orders_logic_type_b(
                self.__instrument,
                self.__params,
                buckets,
                current_price,
                target_range=10,
            )

            for order in new_orders:
                broker.register_order(order)

    def get_current_order_book_time_stamp(self):
        dt = self.current_candle.date_time - timedelta(minutes=self.__sliding_minutes)
        return dt.timestamp()

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
            broker.exit_order(order)

    @staticmethod
    def create_new_orders_logic_type_b(instrument: Instrument, params: dict, buckets: list, current_price: float,
                                       target_range: int):
        buckets = fx_lib.divide_buckets_up_and_down(buckets, current_price)
        long = buckets["long"]
        short = buckets["short"]
        orders = []
        if (len(long) <= target_range + len(params["stopOrders"])) or (
                len(short) <= target_range + len(params["stopOrders"])):
            return orders

        # short order
        for i in range(target_range):
            activatable = True
            for j in range(len(params["stopOrders"])):
                so = params["stopOrders"][j]
                if short[i + j]["shortCountPercent"] < so:
                    activatable = False
                    break
            if activatable:
                enter_price = short[i]["price"] + pips_to_price(instrument, params["spreadAllowance"])
                limit_price = enter_price - pips_to_price(instrument, params["profitDistance"])
                stop_price = enter_price + pips_to_price(instrument, params["stopLossDistance"])
                order = Order(instrument, Side.SELL, Type.MARKET_IF_TOUCHED, 1, enter_price, limit_price, stop_price)
                order.memo = short[i]
                order.memo2 = short[i + 1]
                order.memo3 = short[i + 2]
                orders.append(order)
                break

        # long orders
        for i in range(target_range):
            activatable = True
            for j in range(len(params["stopOrders"])):
                lo = params["stopOrders"][j]
                if long[i + j]["longCountPercent"] < lo:
                    activatable = False
                    break
            if activatable:
                enter_price = long[i]["price"] - pips_to_price(instrument, params["spreadAllowance"])
                limit_price = enter_price + pips_to_price(instrument, params["profitDistance"])
                stop_price = enter_price - pips_to_price(instrument, params["stopLossDistance"])
                order = Order(instrument, Side.BUY, Type.MARKET_IF_TOUCHED, 1, enter_price, limit_price, stop_price)
                order.memo = long[i]
                order.memo2 = long[i + 1]
                order.memo3 = long[i + 2]
                orders.append(order)
                break

        return orders


if __name__ == "__main__":
    # read order books from json file.
    order_books_json = open("../data/order_book/NZD_USD_OB_2020-01-01_2021-01-01.json")
    # read candles from csv file.
    with open("../data/candles/NZD_USD_15S_2020-01-01_2021-01-01.csv", "r") as read_obj:
        feed = list(reader(read_obj))

    order_books = json.load(order_books_json)

    params = {
        "spreadAllowance": -2.2,
        "profitDistance": 14,
        "stopLossDistance": 9,
        "stopOrders_1": 0.7,
        "stopOrders_2": 1.1,
        "stopOrders_3": 1.1,
    }

    my_strategy = NU3BStrategy(order_books, params)
    cerebro = Cerebro(feed, my_strategy)
    print("Start back test.")
    start = time.time()
    cerebro.run()
    cerebro.recorder.aggregate()
    print("Execution time: {}".format(time.time() - start))
    print("Total number of trades: {}".format(cerebro.recorder.total_number_of_trades))
    print("Total total_profit_pips: {} pips".format(cerebro.recorder.total_pips))
    print("Win rate: {}".format(cerebro.recorder.win_rate))
