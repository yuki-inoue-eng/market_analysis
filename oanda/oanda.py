from datetime import datetime
from oandapyV20 import API
from oandapyV20 import V20Error
import oandapyV20.endpoints.instruments as instruments
import math
import pandas as pd
import asyncio
import time
import logging


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
                "from": datetime.utcfromtimestamp(_from).isoformat() + "Z",
                "to": datetime.utcfromtimestamp(_to).isoformat() + "Z",
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
        df.columns = ["DateTime", "Open", "High", "Low", "Close", "Volume"]
        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        return df

    def get_order_books(self, instrument: str, date_from: datetime, date_to: datetime, vicinity: bool):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.__get_order_books_base_async(instrument, date_from, date_to, vicinity))
        results = [r for r in results if r is not None]
        books = []
        for r in results:
            books.append(self.__convert_book_str_to_book_number(r))
        return books  # None を除いた order book を返却

    async def __get_order_books_base_async(self, instrument: str, date_from: datetime, date_to: datetime,
                                           vicinity: bool):
        # date_from 以降で最新の order book スナップショットが取られる時間を計算
        timestamp_from = math.floor(date_from.timestamp())
        timestamp_to = math.floor(date_to.timestamp())
        SNAP_SHOT_INTERVAL_S = 1200
        start_unix_time = timestamp_from + (SNAP_SHOT_INTERVAL_S - timestamp_from % SNAP_SHOT_INTERVAL_S)

        # order_book を取得する時間の一覧
        snap_shot_times = []
        time = start_unix_time
        while timestamp_to - time > 0:
            snap_shot_times.append(datetime.utcfromtimestamp(time))
            time += SNAP_SHOT_INTERVAL_S

        # task の作成
        tasks = [self.__get_order_book(instrument, t, vicinity) for t in snap_shot_times]
        results = await asyncio.gather(*tasks)  # *List とすることで、アンパックしている
        return results

    async def __get_order_book(self, instrument: str, date_time: datetime, vicinity: bool):
        params = {
            "time": date_time.isoformat() + "Z"
        }
        r = instruments.InstrumentsOrderBook(instrument, params)
        try:
            resp = self.__recursive_request(r)  # レスポンスが返却されるまで一時停止する
        except V20Error as err:
            http_status_not_found = 404
            if err.code == http_status_not_found:
                return None
            logging.error(err.msg)
            return None
        if vicinity:
            range_n = 25
            price = float(resp["orderBook"]["price"])
            resp["orderBook"]["buckets"] = self.__extract_book_buckets_vicinity_of_price(
                resp["orderBook"]["buckets"],
                price,
                range_n)
        return resp["orderBook"]

    def get_position_books(self, instrument: str, date_from: datetime, date_to: datetime, vicinity: bool):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.__get_position_books_base_async(instrument, date_from, date_to, vicinity))
        results = [r for r in results if r is not None]
        books = []
        for r in results:
            books.append(self.__convert_book_str_to_book_number(r))
        return books  # None を除いた order book を返却

    async def __get_position_books_base_async(self, instrument: str, date_from: datetime, date_to: datetime,
                                             vicinity: bool):
        # date_from 以降で最新の position book スナップショットが取られる時間を計算
        timestamp_from = math.floor(date_from.timestamp())
        timestamp_to = math.floor(date_to.timestamp())
        SNAP_SHOT_INTERVAL_S = 1200
        start_unix_time = timestamp_from + (SNAP_SHOT_INTERVAL_S - timestamp_from % SNAP_SHOT_INTERVAL_S)

        # position_book を取得する時間の一覧
        snap_shot_times = []
        time = start_unix_time
        while timestamp_to - time > 0:
            snap_shot_times.append(datetime.utcfromtimestamp(time))
            time += SNAP_SHOT_INTERVAL_S

        # task の作成
        tasks = [self.__get_position_book(instrument, t, vicinity) for t in snap_shot_times]
        results = await asyncio.gather(*tasks)  # *List とすることで、アンパックしている
        return results

    async def __get_position_book(self, instrument: str, date_time: datetime, vicinity: bool):
        params = {
            "time": date_time.isoformat() + "Z"
        }
        r = instruments.InstrumentsPositionBook(instrument, params)
        try:
            resp = self.__recursive_request(r)
        except V20Error as err:
            http_status_not_found = 404
            if err.code == http_status_not_found:
                return None
            logging.error(err.msg)
            return None
        if vicinity:
            range_n = 25
            price = float(resp["positionBook"]["price"])
            resp["positionBook"]["buckets"] = self.__extract_book_buckets_vicinity_of_price(
                resp["positionBook"]["buckets"],
                price,
                range_n)
            return resp["positionBook"]

    def __recursive_request(self, request):
        try:
            resp = self.__api.request(request)
        except V20Error as err:
            http_status_too_many_requests = 429
            if err.code == http_status_too_many_requests:
                time.sleep(1)
                return self.__recursive_request(request)
            raise err
        return resp

    @staticmethod
    def __convert_book_str_to_book_number(book):
        if not ("unixTime" in book):
            date_time = datetime.strptime(book["time"].replace("Z", "") + "+0000", '%Y-%m-%dT%H:%M:%S%z')
            book["unixTime"] = date_time.timestamp()
        book["unixTime"] = float(book["unixTime"])
        book["price"] = float(book["price"])
        book["bucketWidth"] = float(book["bucketWidth"])
        for b in book["buckets"]:
            b["price"] = float(b["price"])
            b["longCountPercent"] = float(b["longCountPercent"])
            b["shortCountPercent"] = float(b["shortCountPercent"])
        return book

    @staticmethod
    def __extract_book_buckets_vicinity_of_price(buckets: list, price: float, n: int):
        central = 0
        for b in buckets:
            if float(b["price"]) > price:
                break
            central += 1
        return buckets[(central - n):(central + n)]

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
