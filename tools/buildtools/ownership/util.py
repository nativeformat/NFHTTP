#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

import json
import sys


def get_ghe_token(file_path, list_of_keys):
    try:
        json_data = open(file_path)
        jdata = json.load(json_data)
        entry = jdata[list_of_keys.pop(0)]
        for key in list_of_keys:
            entry = entry[key]
    except IOError as e:
        print "Could not find token: `{}` at path {} and keys {}".format(
            e, file_path, list_of_keys)
        sys.exit(1)
    return entry
