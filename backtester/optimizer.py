from .cerebro import Cerebro
from itertools import product
import concurrent.futures
import numpy as np


class Optimizer:
    def __init__(self, order_books: dict, feed: list, param_ranges: dict, strategy):
        self.feed = feed
        self.strategy = strategy
        self.param_ranges = param_ranges
        self.__convert_param_ranges()
        self.all_params = self.__list_all_params()
        self.order_books = order_books
        self.results = []

    def __convert_param_ranges(self):
        for k, param in self.param_ranges.items():
            if type(param) is list:
                new_param = []
                for p in param:
                    new_param.append(list(np.arange(p["min"], p["max"], p["step"])))
                self.param_ranges[k] = new_param
            elif type(param) is dict:
                self.param_ranges[k] = list(np.arange(param["min"], param["max"], param["step"]))

    def __list_all_params(self):
        key_list = []
        p_list = []
        print(self.param_ranges)
        for key, p_range in self.param_ranges.items():
            key_list.append(key)
            p_list.append(p_range)
        p_prod = list(product(*p_list))
        all_params = []
        for params in p_prod:
            p = {}
            for j in range(len(key_list)):
                p[key_list[j]] = params[j]
            all_params.append(p)
        return all_params

    def optimize(self):
        print("number of pattern: {}".format(len(self.all_params)))
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.__cerebro_run, params) for params in self.all_params]
            concurrent.futures.wait(futures)  # futures が持つの全てのタスクの完了を待機する
            for future in futures:
                self.results.append(future.result())
        sorted(self.results, key=lambda x: x["total_pips"], reverse=True)

    def __cerebro_run(self, params):
        cerebro = Cerebro(self.feed, self.strategy(self.order_books, params))
        cerebro.run()
        cerebro.recorder.aggregate()
        result = {}
        for key, param in params.items():
            result[key] = param
        result["total_pips"] = cerebro.recorder.total_pips
        result["total_number_of_trades"] = cerebro.recorder.total_number_of_trades
        result["win_rate"] = cerebro.recorder.win_rate
        return result

    def export_csv(self):
        pass

    def print_result(self):
        for result in self.results:
            print(result)

    # @staticmethod
    # def list_prod(param):
    #     if type(param) is list:
    #         return list(product(*param))
    #     return param

# if __name__ == "__main__":
#     params = {
#         "hoge": {"min": 1, "max": 4, "step": 1},
#         "foo": {"min": 4, "max": 7, "step": 1},
#         "zoe": {"min": 7, "max": 10, "step": 1}
#     }
#     op = BaseOptimizer({}, params, None)
#     print(op.all_params)
