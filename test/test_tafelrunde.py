from tafelrunde.benchmark import BenchmarkSuite
import time
import random

s = BenchmarkSuite("testbench")

@s.arg_filler
def test_different_maximums(metafunc):
    if "maximum" in metafunc.free_args:
        for maximum in [10, 100, 1000, 10000]:
            metafunc.add_call(maximum = maximum)
    elif "a" in metafunc.free_args and "b" in metafunc.free_args:
        arg_values = {"a": range(0, 30, 10), "b": range(50,70,10)}
        metafunc.call_combinations(arg_values)

@s.bench_func
def add_up(a, b):
    if a > 0:
        return 1 + add_up(a-1, b)
    elif b > 0:
        return 1 + add_up(a, b -1)
    else:
        return 0

@s.warmup(add_up)
def warmup_add_up_func():
    add_up(99, 9)

@s.bench_func
def calculate_unreasonably(maximum):
    acc = 0
    end_time = time.time() + maximum / 2000.
    while time.time() < end_time:
        time.sleep(random.random() * 0.0001)
        acc += 1

    mylist = list(range(acc))

s()
