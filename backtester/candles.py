from datetime import datetime, date


class Candle:
    def __init__(self, candle: list):
        self.date_time = datetime.strptime(candle[0], '%Y-%m-%d %H:%M:%S')
        self.open = float(candle[1])
        self.high = float(candle[2])
        self.low = float(candle[3])
        self.close = float(candle[4])
        self.volume = float(candle[5])

    def is_include(self, price: float):
        return self.high > price > self.low

    def is_holiday(self):
        today = self.date_time.date()
        day_of_the_week = today.strftime("%A")
        is_holiday = day_of_the_week == "Saturday" or day_of_the_week == "Sunday"
        is_christmas = today.month == 12 and today.day == 25
        return is_holiday or is_christmas
