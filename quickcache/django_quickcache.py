from __future__ import absolute_import
from __future__ import unicode_literals
from collections import namedtuple

from django.core.cache import caches
from .quickcache import ConfigMixin, get_quickcache, assert_function
from .cache_helpers import CacheWithPresets, TieredCache
from .quickcache_helper import QuickCacheHelper


class DjangoQuickCache(namedtuple('DjangoQuickCache', [
    'vary_on',
    'skip_arg',
    'timeout',
    'memoize_timeout',
    'helper_class',
    'assert_function',
    'session_function',
]), ConfigMixin):

    def call(self):
        cache = tiered_django_cache([('locmem', self.memoize_timeout, self.session_function),
                                     ('default', self.timeout, None)])
        return get_quickcache(
            cache=cache,
            vary_on=self.vary_on,
            skip_arg=self.skip_arg,
            helper_class=self.helper_class,
            assert_function=self.assert_function,
        ).call()


def tiered_django_cache(cache_with_preset_arg_lists):
    return TieredCache([
        CacheWithPresets(caches[cache_name], timeout, session_function)
        for cache_name, timeout, session_function in cache_with_preset_arg_lists
        if timeout
    ])


get_django_quickcache = DjangoQuickCache(
    vary_on=Ellipsis,
    skip_arg=None,
    timeout=Ellipsis,
    memoize_timeout=Ellipsis,
    helper_class=QuickCacheHelper,
    assert_function=assert_function,
    session_function=None,
).but_with
