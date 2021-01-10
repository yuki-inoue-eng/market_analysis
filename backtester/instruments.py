from enum import Enum


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
    if instrument == Instrument.USD_JPY:
        return price * 100
    elif instrument == Instrument.EUR_JPY:
        return price * 100
    elif instrument == Instrument.AUD_JPY:
        return price * 100
    elif instrument == Instrument.GBP_JPY:
        return price * 100
    elif instrument == Instrument.EUR_USD:
        return price * 10000
    elif instrument == Instrument.GBP_USD:
        return price * 10000
    elif instrument == Instrument.AUD_USD:
        return price * 10000
    elif instrument == Instrument.NZD_USD:
        return price * 10000
    elif instrument == Instrument.EUR_GBP:
        return price * 10000
