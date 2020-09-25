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


def retry_deferred(*retry_args, **retry_kwargs):
    """
    Wrap a test method that may or may not return a Deferred
    result and ensure the underlying behavior honors the retry
    parameters. Honors the same parameters as ``retry``.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            retried = retry(*retry_args, **retry_kwargs)(f)
            # invoke the function using retries
            result = retried(*args, **kwargs)
            # if the result is a Deferred, wrap the inner
            # callback(s) in retries
            if isinstance(result, Deferred):
                result.callbacks[:] = [
                    (
                        (
                            retry(*retry_args, **retry_kwargs)(callback),
                            callbackArgs,
                            callbackKeywords,
                        ),
                        errback_spec,
                    )
                    for (
                        callback, callbackArgs, callbackKeywords),
                    errback_spec in result.callbacks
                ]
            return result
        return wrapper
    return decorator


def test_deferred(f):
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


class DeferredsTests(unittest.TestCase):
    @retry_deferred(reraise=True, stop=stop_after_attempt(12))
    @test_deferred
    def test_simple_exception(self):
        flaky_exception()

    @retry_deferred(reraise=True, stop=stop_after_attempt(12))
    @test_deferred
    def test_simple_failure(self):
        flaky_fail(self)
