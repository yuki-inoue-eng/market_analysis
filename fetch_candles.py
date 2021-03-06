# -*- coding: utf-8 -*-
if __name__ == '__main__':
    import configparser
    import datetime
    import time
    from oanda import Client

    config = configparser.ConfigParser()
    config.read("./oanda_config.txt")
    api_key = config["Practice"]["api_key"]
    oanda = Client(api_key, "", "practice")
    date_from = datetime.datetime(2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    date_to = datetime.datetime(2021, 1, 16, 0, 0, tzinfo=datetime.timezone.utc)
    start = time.time()
    candles_df = oanda.get_candles("NZD_USD", date_from, date_to, "S5")
    elapsed_time = time.time() - start
    print(elapsed_time)
    candles_df.columns = ["DateTime", "Open", "High", "Low", "Close", "Volume"]
    candles_df.to_csv("./data/candles/NZD_USD_S5_2020.csv", index=False)