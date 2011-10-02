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

@s.bench_func
def add_up(a, b):
    if a + b % 5 == 0:
        raise ValueError("a and b is divisible through 5")
    return a + b

@s.warmup(add_up)
def warmup_add_up_func():
    add_up(99, 9)

@s.bench_func
def calculate_unreasonably(maximum):
    acc = 0
    end_time = time.time() + maximum / 20000
    while time.time() < end_time:
        time.sleep(random.random() * 0.0001)
        acc += 1

s()
