from setuptools import setup

setup(name='ownership',
      version='1',
      author='NYC-Infra',
      author_email='nyc-infra-squad@spotify.com',
      url='https://wiki.spotify.net/wiki/Python_packaging_policy',
      description='See README.md',
      scripts=['ownership.py'],
      setup_requires=['flake8', 'nose', 'PyYAML'],
      test_suite='nose.collector')
