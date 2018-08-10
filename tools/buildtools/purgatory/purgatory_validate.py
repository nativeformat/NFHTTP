#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016 Spotify AB

import sys
import yaml


class PurgatoryValidationException(Exception):
    pass


def validate(purgatory,
             required=['added_at', 'jira', 'owner', 'reason', 'test']):
    i = 1
    for entry in purgatory:
        # check required key values are present
        for k in required:
            if not entry.get(k):
                raise PurgatoryValidationException(
                    "Purgatory entry '{}' error - key '{}' must be specified!"
                    .format(i, k))
        # check no extra keys are present
        for k in entry.keys():
            if not k in required:
                raise PurgatoryValidationException(
                    "Purgatory entry '{}' error - key '{}' is unknown!"
                    .format(i, k))
        i += 1
    return True

if __name__ == '__main__':
    with open(sys.argv[1], mode='r') as stream:
        purgatory = yaml.load_all(stream)

        try:
            validate(purgatory)
            print 'success'
        except PurgatoryValidationException as err:
            sys.stderr.write('{}'.format(err))
            exit(1)
