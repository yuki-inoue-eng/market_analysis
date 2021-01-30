from .cerebro import Cerebro
from .instruments import Instrument
from itertools import product
import concurrent.futures
import numpy as np
import pandas as pd
import os
import copy


class Optimizer:
    def __init__(self, feed: list, strategy, instrument: Instrument, param_ranges: dict, order_books: dict,
                 position_books: dict):
        self.feed = feed
        self.strategy = strategy
        self.instrument = instrument
        self.param_ranges_dict = copy.copy(param_ranges)
        self.param_ranges = param_ranges
        self.__convert_param_ranges()
        self.all_params = self.__list_all_params()
        self.order_books = order_books
        self.position_books = position_books
        self.results = []
        self.result_dir_name = "default"

    def __convert_param_ranges(self):
        for k, param in self.param_ranges.items():
            if type(param) is bool:
                self.param_ranges[k] = [param]
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
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(self.cerebro_run, self.all_params[i], i) for i in range(len(self.all_params))]
            concurrent.futures.wait(futures)  # futures が持つの全てのタスクの完了を待機する
            for future in futures:
                self.results.append(future.result())
        self.results = sorted(self.results, key=lambda x: x["total_pips"])
        self.export()

    def cerebro_run(self, params, cerebro_no: int):
        cerebro = Cerebro(self.feed, self.strategy(self.instrument, params, self.order_books, self.position_books),
                          cerebro_no, False)
        cerebro.run()
        result = {}
        for key, param in params.items():
            result[key] = param
        result["total_pips"] = cerebro.recorder.total_pips
        result["total_number_of_trades"] = cerebro.recorder.total_number_of_trades
        # result["win_rate"] = cerebro.recorder.win_rate
        return result

    def export(self):
        export_dir = "../result_data/optimize_data/{}".format(self.result_dir_name)
        os.makedirs(export_dir, exist_ok=True)

        # result
        headers = []
        for key in self.results[0].keys():
            headers.append(key)
        optimize_results = []
        for result in self.results:
            optimize_result = []
            for key in headers:
                optimize_result.append(result[key])
            optimize_results.append(optimize_result)
        pd.DataFrame(optimize_results, columns=headers).to_csv(export_dir + "/result.csv", index=False)

        # params
        headers = ["min", "max", "step"]
        indexes = []
        results = []
        for key, val in self.param_ranges_dict.items():
            indexes.append(key)
            result = []
            if type(val) is dict:
                for header in headers:
                    result.append(val[header])
            elif type(val) is bool:
                result.append(val)
            results.append(result)
        pd.DataFrame(results, columns=headers, index=indexes).to_csv(export_dir + "/param_ranges.csv")

    def print_result(self):
        for result in self.results:
            print(result)

# if __name__ == "__main__":
#     params = {
#         "hoge": {"min": 1, "max": 4, "step": 1},
#         "foo": {"min": 4, "max": 7, "step": 1},
#         "zoe": {"min": 7, "max": 10, "step": 1}
#     }
#     op = BaseOptimizer({}, params, None)
#     print(op.all_params)
