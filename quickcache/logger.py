from __future__ import absolute_import
from __future__ import unicode_literals
import logging


logger = logging.getLogger('quickcache')


def assert_function(assertion, message):
    if assertion:
        logger.warn(message)
