import random
import functools
from jaraco.functools import retry

from twisted.internet.defer import Deferred
from twisted.internet import reactor
from twisted.trial import unittest

flaky_rate = .3


def flaky_exception():
    if random.random() < flaky_rate:
        raise ValueError("flaky exception")


def flaky_fail(test):
    random.random() < flaky_rate and test.fail("flaky fail")


class ThingsTest(unittest.TestCase):
    @retry(retries=11, trap=Exception)
    def test_simple_exception(self):
        flaky_exception()

    @retry(retries=11, trap=Exception)
    def test_simple_failure(self):
        flaky_fail(self)

    @retry(retries=11, trap=Exception)
    def test_simple_assertion(self):
        if random.random() < flaky_rate:
            assert False, "flaky assertion"


def make_callback(f):
    return lambda result, *args, **kwargs: f(*args, **kwargs)


def retry_deferred(*retry_args, **retry_kwargs):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            retried = retry(*retry_args, **retry_kwargs)(f)
            result = retried(*args, **kwargs)
            if isinstance(result, Deferred):
                new = Deferred()
                cb_retried = retry(*retry_args, **retry_kwargs)(result.callback)
                new.addCallback(cb_retried, *args, **kwargs)
                return new
            return result
        return wrapper
    return decorator


def test_deferred(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        result = Deferred()
        reactor.callLater(.1, result.callback, None)
        result.addCallback(make_callback(f), *args, **kwargs)
        return result
    return wrapper


class DeferredsTests(unittest.TestCase):
    @retry_deferred()
    @test_deferred
    def test_simple_exception(self):
        flaky_exception()

    @retry_deferred()
    @test_deferred
    def test_simple_failure(self):
        flaky_fail(self)
