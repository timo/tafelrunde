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
        arg_values = {"a": range(0, 3), "b": range(5,7)}
        metafunc.call_combinations(arg_values)

@s.warmup
def warm_up():
    add_up(99, 9)

@s.bench_func
def add_up(a, b):
    return a + b

@s.bench_func
def calculate_unreasonably(maximum):
    acc = 0
    for i in range(maximum):
        time.sleep(random.random() * 0.0001)
        acc += i
    acc = 0
    for i in range(maximum):
        time.sleep(random.random() * 0.0001)
        acc += i

s()
