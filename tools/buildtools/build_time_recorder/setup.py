from setuptools import setup

setup(name='build_time_recorder',
      version='1',
      author='NYC-Infra',
      author_email='nyc-infra-squad@spotify.com',
      url='https://wiki.spotify.net/wiki/Python_packaging_policy',
      description='See README.md',
      scripts=['build_time_recorder.py'],
      setup_requires=['flake8', 'nose'],
      test_suite='nose.collector')
