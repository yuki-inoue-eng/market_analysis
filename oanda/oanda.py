from datetime import datetime
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import math


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

    def get_candles_s5(self, instrument: str, date_from: datetime, date_to: datetime):
        timestamp_from = math.floor(date_from.timestamp())
        timestamp_to = math.floor(date_to.timestamp())
        print(timestamp_from)
        print(timestamp_to)
        print("hogeaaaaaaaaa")
        candles = []
        while timestamp_to - timestamp_from > 0:
            print("destance" + str(timestamp_to - timestamp_from))
            print("hoge" + str(timestamp_from))
            _from = timestamp_from
            _to = timestamp_from + 5000 * 5
            if _to > timestamp_to:
                _to = timestamp_to
            params = {
                "from": datetime.fromtimestamp(_from).isoformat(),
                "to": datetime.fromtimestamp(_to).isoformat(),
                "granularity": "S5"
            }
            r = instruments.InstrumentsCandles(instrument, params)
            resp = self.__api.request(r)
            candles.append(resp["candles"])
            timestamp_from = _to
        data = []
        for candle in candles:
            data.append([
                candle["time"],
                # datetime.fromisoformat(candle["time"][:19]),
                candle["mid"]["o"],
                candle["mid"]["h"],
                candle["mid"]["l"],
                candle["mid"]["c"],
                candle["volume"],
            ])
        return data


def foge():
    print("hoge")
