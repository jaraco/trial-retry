import random

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
    def test_simple_exception(self):
        flaky_exception()

    def test_simple_failure(self):
        flaky_fail(self)

    def test_simple_assertion(self):
        if random.random() < flaky_rate:
            assert False, "flaky assertion"


def make_callback(f):
    return lambda result, *args, **kwargs: f(*args, **kwargs)


class DeferredsTests(unittest.TestCase):
    def test_simple_exception(self):
        result = Deferred()
        reactor.callLater(.1, result.callback, None)
        result.addCallback(make_callback(flaky_exception))
        return result

    def test_simple_failure(self):
        result = Deferred()
        reactor.callLater(.1, result.callback, None)
        result.addCallback(make_callback(flaky_fail), test=self)
        return result
