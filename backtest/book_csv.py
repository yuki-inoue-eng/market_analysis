import json
import math
import os
import pandas as pd
from oanda import fx_lib
from datetime import datetime, timezone, timedelta


class BookCSVExporter:
    def __init__(self, date_from: datetime, date_to: datetime, order_book: dict, position_book: dict):
        self.date_from = date_from
        self.date_to = date_to
        self.order_books = order_book
        self.position_books = position_book

    @staticmethod
    def __book_is_exist(book: dict, ts_str: str):
        return ts_str in book and len(book[ts_str]["buckets"]) > 0

    def order_book_is_exist(self, timestamp):
        timestamp_str = str(math.floor(timestamp))
        return self.__book_is_exist(self.order_books, timestamp_str)

    def position_book_is_exist(self, timestamp):
        timestamp_str = str(math.floor(timestamp))
        return self.__book_is_exist(self.position_books, timestamp_str)

    def order_book(self, timestamp):
        timestamp_str = str(math.floor(timestamp))
        if self.__book_is_exist(self.order_books, timestamp_str):
            return self.order_books[timestamp_str]
        return None

    def position_book(self, timestamp):
        timestamp_str = str(math.floor(timestamp))
        if self.__book_is_exist(self.position_books, timestamp_str):
            return self.position_books[timestamp_str]
        return None

    def export_csv(self, f_name: str):
        date_from = self.date_from
        header = ["date_time", "price", "limit_short", "stop_short", "limit_long", "stop_long", "gan_short",
                  "loss_short", "gan_long", "loss_long"]
        records = []
        while date_from <= self.date_to:
            record = [date_from, -1, -1, -1, -1, -1, -1, -1, -1, -1]
            timestamp = date_from.timestamp()
            if self.order_book_is_exist(timestamp):
                order_book = self.order_book(timestamp)
                record[1] = order_book["price"]
                buckets = fx_lib.divide_buckets_up_and_down(order_book["buckets"], order_book["price"])
                limit_short = 0
                stop_short = 0
                limit_long = 0
                stop_long = 0
                for i in range(10):
                    limit_short += buckets["high"][i]["shortCountPercent"]
                    stop_short += buckets["low"][i]["shortCountPercent"]
                    limit_long += buckets["low"][i]["longCountPercent"]
                    stop_long += buckets["high"][i]["longCountPercent"]
                record[2] = limit_short
                record[3] = stop_short
                record[4] = limit_long
                record[5] = stop_long
            if self.position_book_is_exist(timestamp):
                position_book = self.position_book(timestamp)
                record[1] = position_book["price"]
                buckets = fx_lib.divide_buckets_up_and_down(position_book["buckets"], position_book["price"])
                gan_short = 0
                loss_short = 0
                gan_long = 0
                loss_long = 0
                for i in range(10):
                    gan_short += buckets["high"][i]["shortCountPercent"]
                    loss_short += buckets["low"][i]["shortCountPercent"]
                    gan_long += buckets["low"][i]["longCountPercent"]
                    loss_long += buckets["high"][i]["longCountPercent"]
                record[6] = gan_short
                record[7] = loss_short
                record[8] = gan_long
                record[9] = loss_long
            records.append(record)
            date_from = date_from + timedelta(minutes=20)
        export_dir = "../result_data/book_csv/"
        os.makedirs(export_dir, exist_ok=True)
        pd.DataFrame(records, columns=header).to_csv(export_dir + f_name, index=False)


if __name__ == "__main__":

    instrument = "NZD_USD"
    d_from = "2019-01-01"
    d_to = "2020-01-01"

    d_from_year = int(d_from.split("-")[0])
    d_from_month = int(d_from.split("-")[1])
    d_from_date = int(d_from.split("-")[2])
    date_from = datetime(d_from_year, d_from_month, d_from_date, 0, 0, tzinfo=timezone.utc)
    d_to_year = int(d_to.split("-")[0])
    d_to_month = int(d_to.split("-")[1])
    d_to_date = int(d_to.split("-")[2])
    date_to = datetime(d_to_year, d_to_month, d_to_date, 0, 0, tzinfo=timezone.utc)

    # read books from json file.
    order_books_json = open("../data/order_book/{}_OB_{}_{}.json".format(instrument, d_from, d_to))
    order_books = json.load(order_books_json)
    position_books_json = open("../data/position_book/{}_OB_{}_{}.json".format(instrument, d_from, d_to))
    position_books = json.load(position_books_json)

    exporter = BookCSVExporter(date_from, date_to, order_books, position_books)
    exporter.export_csv("{}_{}_{}.csv".format(instrument, d_from, d_to))
