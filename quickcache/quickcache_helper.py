from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import hashlib
import inspect
from inspect import isfunction
from collections import namedtuple

from .logger import logger
from .native_utc import utc
import six
from six.moves import map


class QuickCacheHelper(object):
    def __init__(self, fn, vary_on, cache, skip_arg=None, assert_function=None):

        self.fn = fn
        self.cache = cache
        self.prefix = '{}.{}'.format(
            fn.__name__[:40] + (fn.__name__[40:] and '..'),
            self._hash(inspect.getsource(fn), 8)
        )

        arg_names = inspect.getargspec(self.fn).args
        if not isfunction(vary_on):
            vary_on = [part.split('.') for part in vary_on]
            vary_on = [(part[0], tuple(part[1:])) for part in vary_on]
            for arg, attrs in vary_on:
                if arg not in arg_names:
                    raise ValueError(
                        'We cannot vary on "{}" because the function {} has '
                        'no such argument'.format(arg, self.fn.__name__)
                    )

        self.encoding_assert = assert_function

        self.vary_on = vary_on

        if skip_arg is None or isinstance(skip_arg, six.string_types) or isfunction(skip_arg):
            self.skip_arg = skip_arg
        else:
            raise ValueError("skip_arg must be None, a string, or a function")

        arg_spec = inspect.getargspec(self.fn)
        if isinstance(skip_arg, six.string_types) and self.skip_arg not in arg_spec.args:
            raise ValueError(
                'We cannot use "{}" as the "skip" parameter because the function {} has '
                'no such argument'.format(self.skip_arg, self.fn.__name__)
            )

        if not isfunction(self.vary_on):
            for arg, attrs in self.vary_on:
                if arg == self.skip_arg:
                    raise ValueError(
                        'You cannot use the "{}" argument as a vary on parameter and '
                        'as the "skip cache" parameter in the function: {}'.format(arg, self.fn.__name__)
                    )

    def call(self, *args, **kwargs):
        logger.debug('checking caches for {}'.format(self.fn.__name__))
        key = self.get_cache_key(*args, **kwargs)
        logger.debug(key)
        content = self.cache.get(key, default=Ellipsis)
        if content is Ellipsis:
            logger.debug('cache miss, calling {}'.format(self.fn.__name__))
            content = self.fn(*args, **kwargs)
            self.cache.set(key, content)
        return content

    def get_cached_value(self, *args, **kwargs):
        """
        :returns: The cached value or ``Ellipsis``
        """
        key = self.get_cache_key(*args, **kwargs)
        logger.debug(key)
        return self.cache.get(key, default=Ellipsis)

    def set_cached_value(self, *args, **kwargs):
        """
        Sets the cached value
        """
        key = self.get_cache_key(*args, **kwargs)
        logger.debug(key)
        return namedtuple('Settable', ['to'])(lambda value: self.cache.set(key, value))

    def clear(self, *args, **kwargs):
        key = self.get_cache_key(*args, **kwargs)
        self.cache.delete(key)

    @staticmethod
    def _hash(value, length=32):
        return hashlib.md5(value.encode('utf-8')).hexdigest()[-length:]

    def _serialize_for_key(self, value):
        if isinstance(value, six.text_type):
            return 'u' + self._hash(value)
        elif isinstance(value, bytes):
            # Text and bytes values should generate the same key since users
            # generally intend them to mean the same thing (on Python 2 anyway).
            # If a use case for differentiating them presents itself add a
            # 'lenient_strings=False' option to allow the user to explicitly
            # request the different behaviour.
            try:
                text = value.decode('utf-8')
            except UnicodeDecodeError:
                self.encoding_assert(False, 'Non-utf8 encoded string used as cache vary on')
                return 'u' + hashlib.md5(value).hexdigest()[-32:]
            return 'u' + self._hash(text)
        elif isinstance(value, bool):
            return 'b' + str(int(value))
        elif isinstance(value, six.integer_types + (float,)):
            return 'n' + str(value)
        elif isinstance(value, (list, tuple)):
            return 'L' + self._hash(
                ','.join(map(self._serialize_for_key, value)))
        elif isinstance(value, dict):
            return 'D' + self._hash(
                ','.join(sorted(map(self._serialize_for_key, six.iteritems(value))))
            )
        elif isinstance(value, set):
            return 'S' + self._hash(
                ','.join(sorted(map(self._serialize_for_key, value))))
        elif isinstance(value, datetime.datetime):
            # Cache key equality for datetimes follows python equality. Namely:
            # - Datetimes with different timezones but representing the same point in time are serialized
            #   the same way
            # - Naive datetimes can't cause a cache hit for tz aware datetimes (and vice versa)
            if not value.tzinfo:
                serialized_value = value.isoformat()
            else:
                serialized_value = value.astimezone(utc).isoformat()
            return 'DT{}'.format(serialized_value)
        elif value is None:
            return 'N'
        else:
            raise ValueError('Bad type "{}": {}'.format(type(value), value))

    def get_cache_key(self, *args, **kwargs):
        callargs = inspect.getcallargs(self.fn, *args, **kwargs)
        values = []
        if isfunction(self.vary_on):
            values = self.vary_on(*args, **kwargs)
        else:
            for arg_name, attrs in self.vary_on:
                value = callargs[arg_name]
                for attr in attrs:
                    value = getattr(value, attr)
                values.append(value)
        args_string = ','.join(self._serialize_for_key(value)
                               for value in values)
        if len(args_string) > 150:
            args_string = 'H' + self._hash(args_string)
        return 'quickcache.{}/{}'.format(self.prefix, args_string)

    def skip(self, *args, **kwargs):
        if not self.skip_arg:
            return False
        elif isinstance(self.skip_arg, six.string_types):
            callargs = inspect.getcallargs(self.fn, *args, **kwargs)
            return callargs[self.skip_arg]
        elif isfunction(self.skip_arg):
            return self.skip_arg(*args, **kwargs)
        else:
            assert False, "skip_arg must be None, a string, or a function " \
                          "and this should have been checked in __init__"

    def __call__(self, *args, **kwargs):
        if not self.skip(*args, **kwargs):
            return self.call(*args, **kwargs)
        else:
            content = self.fn(*args, **kwargs)
            key = self.get_cache_key(*args, **kwargs)
            self.cache.set(key, content)
            return content
