#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016 Spotify AB

import json
import os.path
from service_info import ServiceInfo


# The suppled list of service-info.yaml files must be relative to the
# current working directory. This function will create or modify a
# file called .mention-bot in the current working directory.
def write_mentionbot_with_service_info_files(service_info_files):
    mention_bot_file = '.mention-bot'
    print "Updating {} with data from {} service-info files.".format(
        mention_bot_file, len(service_info_files))

    mapping = {}

    for si_path in service_info_files:
        si = ServiceInfo.from_yaml_file(si_path)
        if len(si.mentionbot_users) == 0:
            continue
        basedir = os.path.dirname(si_path)

        paths = si.mentionbot_paths
        if len(paths) == 0:
            paths = ['**/*']

        for user in si.mentionbot_users:
            user_paths = mapping.get(user, [])
            for path in paths:
                path = "{}/{}".format(basedir, path) if basedir else path
                user_paths.append(path)
            mapping[user] = user_paths

    if not os.path.isfile(mention_bot_file):
        with open(mention_bot_file, mode='w') as stream:
            stream.write("{}")

    with open(mention_bot_file, mode='r+') as stream:
        mention_bot_json = json.load(stream)
        if 'alwaysNotifyForPaths' in mention_bot_json:
            del mention_bot_json['alwaysNotifyForPaths']

        if len(mapping) > 0:
            mention_bot_json['alwaysNotifyForPaths'] = []
            for user, paths in mapping.items():
                mention_bot_json['alwaysNotifyForPaths'].append(
                    {'name': user, 'files': paths})

        stream.seek(0)
        json.dump(mention_bot_json, stream, sort_keys=True, indent=4)
        stream.truncate()
