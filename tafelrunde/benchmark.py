"""The benchmark module allows writing rather simple benchmarks for measuring
time and memory consumption of functions.

  .. testsetup::

    from benchmark.benchmark import BenchmarkSuite

>>> s = BenchmarkSuite("demonstration")
>>> @s.arg_filler
... def combine_arguments(metafunc):
...    from itertools import product
...    arg_values = {}
...    if "a" in metafunc.free_args:
...        arg_values["a"] = range(0,3)
...    if "b" in metafunc.free_args:
...        arg_values["b"] = range(5, 7)
...    metafunc.call_combinations(arg_values)
...
>>> @s.bench_func
... def add(a, b):
...    return a + b

After that, a call to your BenchmarkSuite instance will cause the benchmark
to run.

In later versions, the current version of the software being tested will be
determined and benchmark histories will be created.
"""
import os
import sys
import time
import resource

import itertools

_global_arg_filler = None
def global_arg_filler(func):
    global _global_arg_filler
    _global_arg_filler = func
    return func

def argument_combinations(kwargs):
    value_combinations = itertools.product(*kwargs.values())
    kv_tuples = map(lambda value: zip(kwargs.keys(), value), value_combinations)
    dicts = map(dict,kv_tuples)
    return dicts

_free_arg_names = set()
_metafuncs = []
class MetaFunc(object):
    def __init__(self, fn):
        self.fn = fn

        # fn.func_defaults holds the default values for named args,
        # fn.func_code.co_varnames holds the names of all variables.
        # the first vars are args, the first args are free.
        # the rest has default values and will be ignored or are local vars
        if fn.func_defaults:
            self.free_args = fn.func_code.co_varnames[:fn.func_code.co_argcount-len(fn.func_defaults)]
        else:
            self.free_args = fn.func_code.co_varnames[:fn.func_code.co_argcount]
        self.calls = []
        self.func_name = fn.func_name
        if self.free_args:
            _free_arg_names.update(set(self.free_args))
        else:
            self.calls.append({})
        _metafuncs.append(self)

    def add_call(self, **kwargs):
        self.calls.append(kwargs)

    def call_combinations(self, domains):
        for combination in argument_combinations(domains):
            self.add_call(**combination)

    def __repr__(self):
        return "<MetaFunc of %(func_name)s with %(num_calls)d registered calls>" %\
                dict(func_name=self.func_name,
                     num_calls=len(self.calls))

    def __str__(self):
        return repr(self)

    def call_id(self, **kwargs):
        args = map(str, kwargs.values())
        if len(args) == 0:
            return self.func_name
        else:
            return "%s[%s]" % (self.func_name, "][".join(args))

    def __call__(self, **kwargs):
        self.fn(**kwargs)

class Benchmark(object):
    def __init__(self, name):
        self.name = name
        self._warmup = None
        self.function = None

        self.results = {}
        self.arg_filler = _global_arg_filler

    def prepare(self, arg_filler=None):
        if arg_filler is None:
            arg_filler = _global_arg_filler
        if self.function.free_args and not self.function.calls:
            arg_filler(self.function)

    def warmup(self, function):
        self._warmup = function
        return function

    def body(self, function):
        self.function = MetaFunc(function)
        return function

    def __call__(self, **kwargs):
        if self._warmup:
            print "(warmup...",
            sys.stdout.flush()
            self._warmup()
            print "done)"

        for funccall in self.function.calls:
            print self.function.call_id(**funccall)
            starttime = time.time()
            pid = os.fork()
            if pid == 0:
                try:
                    self.function(**funccall)
                    sys.exit(0)
                except:
                    sys.exit(1)
            else:
                (cpid, exit_s, rusage) = os.wait4(pid, 0)
                elapsed_time = time.time() - starttime
                self.results[self.function.call_id(**funccall)] = dict(
                        utime=rusage.ru_utime,
                        stime=rusage.ru_stime,
                        time=elapsed_time,
                        mem_usage=rusage.ru_maxrss * resource.getpagesize())
                print self.results[self.function.call_id(**funccall)]

class BenchmarkSuite(object):
    def __init__(self, name, version_str="1"):
        self.name = name
        self.benchmarks = {}
        self.arg_fill_func = None
        self.version_str = version_str

    def arg_filler(self, func):
        self.arg_fill_func = func
        return func

    def benchmark(self, name):
        bench = Benchmark(name)
        if name in self.benchmarks:
            raise ValueError("The name '%s' is already used in %s!" % (name, self.name))
        self.benchmarks[name] = bench
        return bench

    def bench_func(self, func):
        bench = self.benchmark(func.func_name)
        bench.body(func)
        return func

    def warmup(self, bench_func):
        def wrapper(func):
            return self.benchmarks[bench_func.func_name].warmup(func)
        return wrapper

    def __call__(self):
        for benchmark in self.benchmarks.values():
            benchmark.prepare(self.arg_fill_func)
        print "Running Benchmark Suite %s (version %s)" % (self.name,self.version_str)
        print "-" * 40
        for bench in self.benchmarks.values():
            print "Running benchmark %s" % (bench.name,)
            print "-" *  30
            bench()
