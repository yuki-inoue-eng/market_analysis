from datetime import datetime
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import math
import pandas as pd


class Client:
    def __init__(self, api_key, account_id, env):
        # 接頭辞にアンスコ(_)付きの変数名はプライベート変数だが、あくまで紳士協定
        # 接頭辞にアンスコ*2(__)をつけると外からアクセスできなくなる
        if env == "Trade" or env == "trade":
            self.__env = "trade"
        else:
            self.__env = "practice"
        self.__api = API(api_key, self.__env)
        self.__account_id = account_id

    def get_candles(self, instrument: str, date_from: datetime, date_to: datetime, granularity: str):
        timestamp_from = math.floor(date_from.timestamp())
        timestamp_to = math.floor(date_to.timestamp())
        granularity_s = self.__get_granularity_s(granularity)
        candles = []
        while timestamp_to - timestamp_from > 0:
            _from = timestamp_from
            _to = timestamp_from + 5000 * granularity_s
            if _to > timestamp_to:
                _to = timestamp_to
            params = {
                "from": datetime.fromtimestamp(_from).isoformat(),
                "to": datetime.fromtimestamp(_to).isoformat(),
                "granularity": granularity
            }
            r = instruments.InstrumentsCandles(instrument, params)
            resp = self.__api.request(r)
            candles += resp["candles"]
            timestamp_from = _to
        data = []
        for candle in candles:
            data.append([
                datetime.fromisoformat(candle["time"].split(".")[0]),
                candle["mid"]["o"],
                candle["mid"]["h"],
                candle["mid"]["l"],
                candle["mid"]["c"],
                candle["volume"]
            ])
        df = pd.DataFrame(data)
        df.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        return df

    @staticmethod
    def __get_granularity_s(granularity: str):
        if granularity == "S5":
            return 5
        if granularity == "S10":
            return 10
        if granularity == "S15":
            return 15
        if granularity == "S30":
            return 30
        if granularity == "M1":
            return 60
        if granularity == "M2":
            return 120
        if granularity == "M4":
            return 240
        if granularity == "M5":
            return 300
        if granularity == "M10":
            return 600
        if granularity == "M15":
            return 900
        if granularity == "M30":
            return 1800
        if granularity == "H1":
            return 3600
        if granularity == "H2":
            return 7200
        if granularity == "H3":
            return 10800
        if granularity == "H4":
            return 14400
        if granularity == "H6":
            return 21600
        if granularity == "H8":
            return 28800
        if granularity == "H12":
            return 43200
        if granularity == "D":
            return 86400
        if granularity == "W":
            return 604800
