import unittest
import random


flaky_rate = .2


class ThingsTest(unittest.TestCase):
    def test_simple_exception(self):
        if random.random() < flaky_rate:
            raise ValueError("flaky exception")

    def test_simple_failure(self):
        if random.random() < flaky_rate:
            self.fail("flaky fail")

    def test_simple_assertion(self):
        if random.random() < flaky_rate:
            assert False, "flaky assertion"
