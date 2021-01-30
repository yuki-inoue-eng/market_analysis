from oanda import Client
import configparser
import datetime
import time

if __name__ == '__main__':
    # fetch candles params
    d_from = "2019-01-01"
    d_to = "2020-01-01"
    instrument = "NZD_USD"
    granularity = "1T"  # 1D:day, 1H:hour, 1T:minutes, 1S:seconds

    config = configparser.ConfigParser()
    config.read("./oanda_config.txt")
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
    candles_df = oanda.get_candles(instrument, date_from, date_to, "S5")
    elapsed_time = time.time() - start
    candles_df.columns = ["DateTime", "Open", "High", "Low", "Close", "Volume"]
    candles_df = candles_df.set_index("DateTime")
    candles_df = candles_df.resample(granularity).agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })
    candles_df = candles_df.interpolate()
    candles_df.to_csv("./data/candles/{}_{}_{}_{}.csv".format(instrument, granularity, d_from, d_to))
