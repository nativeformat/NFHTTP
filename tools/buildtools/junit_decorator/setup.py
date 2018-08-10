from setuptools import setup

setup(name='junit_decorator',
      version='1',
      author='iOS-Infra',
      author_email='ios-infra-squad@spotify.com',
      url='https://wiki.spotify.net/wiki/Python_packaging_policy',
      description='See README.md',
      scripts=['decorator.py'],
      setup_requires=['xml', 'nose'],
      test_suite='nose.collector')
