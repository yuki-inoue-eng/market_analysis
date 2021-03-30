from oanda import Client
import configparser
import datetime
import json
import time
import math
import os
import sys

if __name__ == '__main__':
    # fetch order books params
    d_from = sys.argv[2]
    d_to = sys.argv[3]
    instrument = sys.argv[1]

    config = configparser.ConfigParser()
    config.read("oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", os.environ['ENV'])
    d_from_year = int(d_from.split("-")[0])
    d_from_month = int(d_from.split("-")[1])
    d_from_date = int(d_from.split("-")[2])
    d_to_year = int(d_to.split("-")[0])
    d_to_month = int(d_to.split("-")[1])
    d_to_date = int(d_to.split("-")[2])
    date_from = datetime.datetime(d_from_year, d_from_month, d_from_date, 0, 0, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(d_to_year, d_to_month, d_to_date, 0, 0, tzinfo=datetime.timezone.utc)
    start = time.time()
    order_books = oanda.get_order_books(instrument, date_from, date_to, True)
    order_books = {math.floor(o["unixTime"]): {"price": o["price"], "buckets": o["buckets"]} for o in order_books}  # 辞書型に変換
    elapsed_time = time.time() - start
    print(elapsed_time)
    with open("./data/order_book/{}_OB_{}_{}.json".format(instrument, d_from, d_to), "w") as f:
        json.dump(order_books, f)
