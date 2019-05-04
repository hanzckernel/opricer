#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='opricer',
    version='0.0.1',
    description='Option Pricing by python',
    author='Zhicheng Han',
    author_email='hanzc.kernel@gmail.com',
    url='https://github.com/hanzckernel/option_pricer',
    packages=find_packages(exclude='tests'),
    license='Unlicense',
    zip_safe=False,
    keywords='opricer',
    test_suite='tests'
)
