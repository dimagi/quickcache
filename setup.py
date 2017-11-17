#!/usr/bin/env python
from __future__ import absolute_import
from setuptools import setup

setup(
    name='quickcache',
    version='0.1.0',
    description='caching has never been easier',
    author='Dimagi',
    author_email='dev@dimagi.com',
    url='https://github.com/dimagi/quickcache',
    packages=['quickcache'],
    test_suite='test_quickcache',
    install_requires=[
        'six==1.11.0',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
