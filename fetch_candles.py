if __name__ == '__main__':
    import configparser
    import datetime
    import time
    from oanda import Client

    config = configparser.ConfigParser()
    config.read("./oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", "practice")
    UTC = datetime.timezone.utc
    date_from = datetime.datetime(2020, 1, 1, 0, 0, tzinfo=UTC)
    date_to = datetime.datetime(2020, 2, 1, 0, 0, tzinfo=UTC)
    start = time.time()
    candles_df = oanda.get_candles("USD_JPY", date_from, date_to, "S5")
    elapsed_time = time.time() - start
    print(elapsed_time)
    candles_df.columns = ["Date Time", "Open", "High", "Low", "Close", "Volume"]
    candles_df.to_csv("./data/candles/USD_JPY_S5_2020.csv", index=False)