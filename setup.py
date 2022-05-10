#!/usr/bin/env python
from setuptools import setup

setup(
    name='quickcache',
    version='0.5.4',
    description='caching has never been easier',
    author='Dimagi',
    author_email='dev@dimagi.com',
    url='https://github.com/dimagi/quickcache',
    packages=['quickcache'],
    test_suite='test_quickcache',
    install_requires=[],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
