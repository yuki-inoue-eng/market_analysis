if __name__ == '__main__':
    import configparser
    import datetime
    from oanda import Client
    import json
    import time
    import math

    config = configparser.ConfigParser()
    config.read("oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", "practice")
    UTC = datetime.timezone.utc
    date_from = datetime.datetime(2020, 12, 13, 0, 0, tzinfo=UTC)
    date_to = datetime.datetime(2021, 1, 13, 0, 0, tzinfo=UTC)
    start = time.time()
    order_books = oanda.get_order_books("NZD_USD", date_from, date_to, True)
    order_books = {math.floor(o["unixTime"]): o["buckets"] for o in order_books}  # 辞書型に変換
    elapsed_time = time.time() - start
    print(elapsed_time)
    with open("./data/order_book/NZD_USD_OB_2020.json", "w") as f:
        json.dump(order_books, f)
