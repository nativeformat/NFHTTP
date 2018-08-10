#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) ${year} Spotify AB

try:
    from spotify_build import setup
except ImportError:
    from setuptools import setup

import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), "lib", "requests"))

setup(
    name='Vulcan',
    version='0.0.1',
    author=u'Daniel Fanjul',
    author_email='dfanjul@spotify.com',
    url='https://wiki.spotify.net/wiki/Python_packaging_policy',
    description='Vulcan, the dependency management system.',
    packages=['spotify_vulcan'],
    scripts=['bin/vulcan.py'],
    test_suite='test'
)
