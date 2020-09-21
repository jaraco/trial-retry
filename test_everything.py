import unittest
import random

from twisted.internet.defer import Deferred


flaky_rate = 1


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


class DeferredsTests(unittest.TestCase):
    def test_simple_exception(self):
        result = Deferred()
        result.addCallback(flaky_exception)
        return result

    def test_simple_failure(self):
        result = Deferred()
        result.addCallback(flaky_fail, self)
        return result
