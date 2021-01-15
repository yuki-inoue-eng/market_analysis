from datetime import datetime
import math
# def new_position(instrument: str, side :str, unit: int, price:float, take_profit: float, stop_loss: float):


def pips_to_price(instrument: str, price: float):
    if instrument == "USD_JPY":
        return price / 100
    if instrument == "EUR_JPY":
        return price / 100
    if instrument == "AUD_JPY":
        return price / 100
    if instrument == "GBP_JPY":
        return price / 100
    if instrument == "EUR_USD":
        return price / 10000
    if instrument == "GBP_USD":
        return price / 10000
    if instrument == "AUD_USD":
        return price / 10000
    if instrument == "NZD_USD":
        return price / 10000
    if instrument == "EUR_GBP":
        return price / 10000
    return 0


def is_order_book_update_time(date_time: datetime):
    return math.floor(date_time.timestamp()) % 1200 == 0


def divide_buckets_up_and_down(buckets: list, price: float):
    central = 0
    for b in buckets:
        if b["price"] > price:
            break
        central += 1
    return {"short": buckets[:central], "long": buckets[central:]}