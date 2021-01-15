from enum import Enum
import math


class Instrument(Enum):
    USD_JPY = "USD_JPY"
    EUR_JPY = "EUR_JPY"
    AUD_JPY = "AUD_JPY"
    GBP_JPY = "GBP_JPY"
    EUR_USD = "EUR_USD"
    GBP_USD = "GBP_USD"
    AUD_USD = "AUD_USD"
    NZD_USD = "NZD_USD"
    EUR_GBP = "EUR_GBP"


def pips_to_price(instrument: Instrument, pips: float):
    if instrument == Instrument.USD_JPY:
        return pips / 100
    elif instrument == Instrument.EUR_JPY:
        return pips / 100
    elif instrument == Instrument.AUD_JPY:
        return pips / 100
    elif instrument == Instrument.GBP_JPY:
        return pips / 100
    elif instrument == Instrument.EUR_USD:
        return pips / 10000
    elif instrument == Instrument.GBP_USD:
        return pips / 10000
    elif instrument == Instrument.AUD_USD:
        return pips / 10000
    elif instrument == Instrument.NZD_USD:
        return pips / 10000
    elif instrument == Instrument.EUR_GBP:
        return pips / 10000


def price_to_pips(instrument: Instrument, price: float):
    pips = 0
    if instrument == Instrument.USD_JPY:
        pips = price * 100
    elif instrument == Instrument.EUR_JPY:
        pips = price * 100
    elif instrument == Instrument.AUD_JPY:
        pips = price * 100
    elif instrument == Instrument.GBP_JPY:
        pips = price * 100
    elif instrument == Instrument.EUR_USD:
        pips = price * 10000
    elif instrument == Instrument.GBP_USD:
        pips = price * 10000
    elif instrument == Instrument.AUD_USD:
        pips = price * 10000
    elif instrument == Instrument.NZD_USD:
        pips = price * 10000
    elif instrument == Instrument.EUR_GBP:
        pips = price * 10000
    return math.ceil(pips*10)/10  # 下二桁を切上
