from oanda import Client
import configparser
import datetime
import time

if __name__ == '__main__':
    # fetch order books params
    d_from = "2021-01-01"
    d_to = "2021-01-02"
    instrument = "USD_JPY"

    config = configparser.ConfigParser()
    config.read("oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", "practice")
    d_from_year = int(d_from.split("-")[0])
    d_from_month = int(d_from.split("-")[1])
    d_from_date = int(d_from.split("-")[2])
    d_to_year = int(d_to.split("-")[0])
    d_to_month = int(d_to.split("-")[1])
    d_to_date = int(d_to.split("-")[2])
    date_from = datetime.datetime(d_from_year, d_from_month, d_from_date, 0, 0, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(d_to_year, d_to_month, d_to_date, 0, 0, tzinfo=datetime.timezone.utc)
    start = time.time()
    order_books = oanda.get_order_books(instrument, date_from, date_to, False)

    for order_book in order_books:
        so = 0
        lo = 0
        for b in order_book["buckets"]:
            so += b["shortCountPercent"]
            lo += b["longCountPercent"]
        print("sum:{}".format(so+lo))


