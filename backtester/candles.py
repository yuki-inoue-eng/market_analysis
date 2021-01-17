from datetime import datetime, timezone
from .orders import Side


class Candle:
    def __init__(self, candle: list):
        self.date_time = datetime.strptime(candle[0]+"+0000", '%Y-%m-%d %H:%M:%S%z')
        self.open = float(candle[1])
        self.high = float(candle[2])
        self.low = float(candle[3])
        self.close = float(candle[4])
        self.volume = float(candle[5])

    def is_include(self, price: float):
        return self.high >= price >= self.low

    def is_touch_stop(self, order_type: Side, stop_price: float):
        if order_type is Side.SELL:
            return self.high >= stop_price
        if order_type is Side.BUY:
            return self.low <= stop_price

    def is_touch_limit(self, order_type: Side, limit_price: float):
        if order_type is Side.SELL:
            return self.low <= limit_price
        if order_type is Side.BUY:
            return self.high >= limit_price

    def is_holiday(self):
        today = self.date_time.date()
        day_of_the_week = today.strftime("%A")
        is_holiday = day_of_the_week == "Saturday" or day_of_the_week == "Sunday"
        is_christmas = today.month == 12 and today.day == 25
        return is_holiday or is_christmas
