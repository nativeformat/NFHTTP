#!/bin/sh

RUN_INTEGRATION_TESTS= PYTHONPATH=lib/requests python -m unittest discover -p '*_test.py' -v
