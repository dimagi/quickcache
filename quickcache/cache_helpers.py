from __future__ import absolute_import

from __future__ import unicode_literals
import warnings
from collections import namedtuple
from .logger import logger


class ForceSkipCache(Exception):
    pass


class CacheWithPresets(namedtuple('CacheWithPresets', ['cache', 'timeout', 'prefix_function'])):

    # make prefix_function optional
    def __new__(cls, cache, timeout, prefix_function=None):
        return super(CacheWithPresets, cls).__new__(cls, cache, timeout, prefix_function)

    def prefixed_key(self, key):
        if self.prefix_function:
            return self.prefix_function() + key
        else:
            return key

    def get(self, key, default=None):
        try:
            return self.cache.get(self.prefixed_key(key), default=default)
        except ForceSkipCache:
            return default

    def set(self, key, value):
        try:
            return self.cache.set(self.prefixed_key(key), value, timeout=self.timeout)
        except ForceSkipCache:
            pass

    def delete(self, key):
        try:
            return self.cache.delete(self.prefixed_key(key))
        except ForceSkipCache:
            pass


class CacheWithTimeout(CacheWithPresets):
    def __new__(cls, cache, timeout):
        warnings.warn("CacheWithTimeout is deprecated. Please use CacheWithPresets instead.",
                      DeprecationWarning)
        return super(CacheWithTimeout, cls).__new__(cls, cache, timeout)


class TieredCache(object):
    """
    Tries a number of caches in increasing order.
    Caches should be ordered with faster, more local caches at the beginning
    and slower, more shared caches towards the end

    Relies on each of the caches' default timeout;
    TieredCache.set doesn't accept a timeout parameter

    """

    def __init__(self, caches):
        self.caches = caches

    def get(self, key, default=None):
        missed = []
        for cache in self.caches:
            content = cache.get(key, default=Ellipsis)
            if content is not Ellipsis:
                for missed_cache in missed:
                    missed_cache.set(key, content)
                logger.debug('missed caches: {}'.format([c.__class__.__name__
                                                         for c in missed]))
                logger.debug('hit cache: {}'.format(cache.__class__.__name__))
                return content
            else:
                missed.append(cache)
        return default

    def set(self, key, value):
        for cache in self.caches:
            cache.set(key, value)

    def delete(self, key):
        for cache in self.caches:
            cache.delete(key)
