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


# 成り行き注文ロジック
class NU4DStrategy(Strategy):
    def __init__(self, order_books: dict, position_books: dict):
        super().__init__()
        self.__order_books = order_books
        self.__position_books = position_books
        self.__sliding_minutes = 5
        self.__instrument = Instrument.NZD_USD
        self.__entered_orders = {}
        self.__params = {
            "nowBuyPosition": 2.0,  # 買いポジションの閾値
            "nowStopOrder": 2.0,  # 現在のストップ売りの閾値(下限)
            "beforeStopOrder": 1.75,  # 直近のストップ売りの閾値(上限)
            "stopLossDistance": 10,  # 損切り幅(pips)

        }

    def on_candle(self, broker: Broker):

        if self.is_lambda_invoke_time() and self.is_restraint_time_zone():
            self.close_all_entered_orders(broker)
        if self.is_lambda_invoke_time() and not self.is_restraint_time_zone():
            current_price = self.current_candle.close
            current_book_time_stamp_str = str(math.floor(self.get_current_book_time_stamp()))
            before_book_time_stamp_str = str(math.floor(self.get_before_book_time_stamp()))

            # TODO: この書き方では、新規注文処理と決済処理を書けないので、それぞれ関数化する必要がある
            # order book と position book が無い場合は処理を抜ける
            if not (current_book_time_stamp_str in self.__order_books) and (
                    before_book_time_stamp_str in self.__order_books) and (
                    current_book_time_stamp_str in self.__position_books):
                return
            if len(broker.get_entered_orders()) == 0:
                new_order = self.__create_new_orders_logic_type_d(
                    self.__instrument,
                    self.__params,
                    self.__position_books[current_book_time_stamp_str],
                    self.__order_books[current_book_time_stamp_str],
                    self.__order_books[before_book_time_stamp_str],
                    current_price,
                    6
                )
                broker.market_enter_order(new_order)




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

    # current_price には ローソク足の終値を入れます
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
        if self.__o_short_is_over(current_o_short, params["nowStopOrder"], target_range)\
                and not self.__o_short_is_over(before_o_short, params["beforeStopOrder"], target_range)\
                and self.__p_bucket_is_over(current_p_low, current_p_high, params["nowBuyPosition"], 3):
            stop_price = current_price - pips_to_price(instrument, params["stopLossDistance"])
            return Order(instrument, Side.BUY, Type.MARKET, 1, None, None, stop_price)

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
