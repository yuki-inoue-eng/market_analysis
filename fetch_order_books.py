if __name__ == '__main__':
    import configparser
    import datetime
    from oanda import Client
    import json

    # import time

    config = configparser.ConfigParser()
    config.read("oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", "practice")
    UTC = datetime.timezone.utc
    date_from = datetime.datetime(2020, 11, 1, 0, 0, tzinfo=UTC)
    date_to = datetime.datetime(2020, 11, 1, 2, 0, tzinfo=UTC)
    # start = time.time()
    order_books = oanda.get_order_books("USD_JPY", date_from, date_to, True)
    # elapsed_time = time.time() - start
    with open("./data/order_book/USD_JPY_OB.json", "w") as fout:
        json.dump(order_books, fout)
