import random
import functools
from tenacity import retry, stop_after_attempt

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
    @retry(reraise=True, stop=stop_after_attempt(12))
    def test_simple_exception(self):
        flaky_exception()

    @retry(reraise=True, stop=stop_after_attempt(12))
    def test_simple_failure(self):
        flaky_fail(self)

    @retry(reraise=True, stop=stop_after_attempt(12))
    def test_simple_assertion(self):
        if random.random() < flaky_rate:
            assert False, "flaky assertion"


def make_callback(f):
    return lambda result, *args, **kwargs: f(*args, **kwargs)


def resolve_deferred(f):
    """
    Wrap a call that may or may not return a Deferred
    result and if a Deferred is returned, synchronize with
    it before returning.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        if isinstance(res, Deferred):
            res = reactor.wait(res)
        return res
    return wrapper


def setup_deferred(f):
    """
    Wrap a synchronous test method to instead return a Deferred
    that is triggered after 100ms.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        result = Deferred()
        reactor.callLater(.1, result.callback, None)
        result.addCallback(make_callback(f), *args, **kwargs)
        return result
    return wrapper


def make_flaky(f):
    """
    Wrap a function to make it flaky before called.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        flaky_exception()
        return f(*args, **kwargs)
    return wrapper


class DeferredsTests(unittest.TestCase):
    @retry(reraise=True, stop=stop_after_attempt(12))
    @resolve_deferred
    @make_flaky
    @setup_deferred
    def test_simple_exception(self):
        flaky_exception()

    @retry(reraise=True, stop=stop_after_attempt(12))
    @resolve_deferred
    @make_flaky
    @setup_deferred
    def test_simple_failure(self):
        flaky_fail(self)
