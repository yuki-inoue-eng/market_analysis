import concurrent.futures
import os
import time

LEARGE_TEXT = "some string" * 10000000


def io_bound(file_name):
    with open(file_name, "w+") as f:
        f.write(LEARGE_TEXT)
        f.seek(0)
        f.read()
    os.remove(file_name)
    return "Future is done!"


def cpu_bound():
    i = 0
    while i < 10000000:
        i = i + 1 - 2 + 3 - 4 + 5
    return "Future is done!"


if __name__ == "__main__":
    # start = time.time()
    # print(io_bound("1.txt"))
    # print(io_bound("2.txt"))
    # end = time.time()
    # print("I/O bound: Sync {:.4f}".format(end - start))
    # print("")
    #
    # with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    #     start = time.time()
    #     future1 = executor.submit(io_bound, "1.txt")
    #     future2 = executor.submit(io_bound, "2.txt")
    #     print(future1.result())
    #     print(future2.result())
    #     end = time.time()
    #     print("I/O bound: Thread  {:.4f}".format(end - start))
    #     print("")
    #
    # with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
    #     start = time.time()
    #     future1 = executor.submit(io_bound, "1.txt")
    #     future2 = executor.submit(io_bound, "2.txt")
    #     print(future1.result())
    #     print(future2.result())
    #     end = time.time()
    #     print("The number of cpu: {}".format(os.cpu_count()))
    #     print("I/O bound: Process  {:.4f}".format(end - start))
    #     print("")

    start = time.time()
    print(cpu_bound())
    print(cpu_bound())
    end = time.time()
    print("CPU bound: Sync {:.4f}".format(end - start))
    print("")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        start = time.time()
        future1 = executor.submit(cpu_bound)
        future2 = executor.submit(cpu_bound)
        print(future1.result())
        print(future2.result())
        end = time.time()
        print("CPU bound: Thread  {:.4f}".format(end - start))
        print("")

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        start = time.time()
        future1 = executor.submit(cpu_bound)
        future2 = executor.submit(cpu_bound)
        print(future1.result())
        print(future2.result())
        end = time.time()
        print("The number of cpu: {}".format(os.cpu_count()))
        print("CPU bound: Process  {:.4f}".format(end - start))
        print("")
