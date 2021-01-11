class Candle:
    def __init__(self, candle: list):
        self.date_time = candle[0]
        self.open = candle[1]
        self.high = candle[2]
        self.low = candle[3]
        self.close = candle[4]
        self.volume = candle[5]

    def is_include(self, price: float):
        return self.high > price and price < self.low
