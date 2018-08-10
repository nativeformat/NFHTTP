#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016 Spotify AB

import httplib
import json

import util

YAML_FILENAME = 'service-info.yaml'
SYSMODEL_HOST = 'sysmodel.spotify.net'
GHE_HOST = 'ghe.spotify.net'


def synchronize_system_z(repo):
    # temp fix for ownership sync because GHE private mode
    # hardcode path to secrets file and get random token from buildagent
    token = util.get_ghe_token('/etc/spotify/secrets.json',
                                    ['buildagent', 'diffbot', 'ghetoken'])

    print "Fetching {} contents from GHE...".format(repo)
    ghe_locations = set(_get_locations_from_ghe(repo, token))

    print "Fetching sysmodel locations...".format(repo)
    sys_locations = set(_get_locations_from_sysmodel(repo))

    to_post = ghe_locations - sys_locations
    for location in to_post:
        print "Posting {}".format(location)
        _post_location_to_sysmodel(location)

    to_delete = sys_locations - ghe_locations
    for location in to_delete:
        print "Deleting {}".format(location)
        _delete_location_from_sysmodel(location)

    return {
        'posted': to_post,
        'deleted': to_delete
    }


class SystemZError(Exception):
    pass


def _get_locations_from_ghe(repo, token):
    loc_prefix = 'ghe:/{}'.format(repo)
    endpoint = '/api/v3/repos/{}/git/trees/HEAD?recursive=1'.format(repo)
    headers = {'Authorization': 'token {}'.format(token)}
    body = _fetch_json(GHE_HOST, endpoint, True, headers)

    locations = []
    for item in body['tree']:
        tp = item['path']
        if tp.endswith(YAML_FILENAME):
            tp = "{}/{}".format(loc_prefix, tp)
            locations.append(tp)

    return locations


def _get_locations_from_sysmodel(repo):
    loc_prefix = 'ghe:/{}'.format(repo)
    body = _fetch_json(SYSMODEL_HOST, '/api/v1/locations')

    locations = []
    for item in body:
        loc = item['location']
        if loc.startswith(loc_prefix) and loc.endswith(YAML_FILENAME):
            locations.append(loc)

    return locations


def _post_location_to_sysmodel(location):
    payload = {'location': location}
    body = json.dumps(payload)

    _make_request(
        'POST', SYSMODEL_HOST, '/api/v1/locations', headers=None,
        https=False, body=body)
    return True


def _delete_location_from_sysmodel(location):
    ep = '/api/v1/locations/{}'.format(location)
    _make_request(
        'DELETE', SYSMODEL_HOST, ep, headers=None, https=False)
    return True


def _fetch_json(host, endpoint, https=False, headers=None):
    response = _make_request('GET', host, endpoint, headers, https)
    return json.loads(response.read())


def _make_request(method, host, endpoint, headers=None, https=False, body=None):  # NOQA
    conn = None
    if https:
        conn = httplib.HTTPSConnection(host)
    else:
        conn = httplib.HTTPConnection(host)

    if headers:
        conn.request(method, endpoint, body, headers)
    else:
        conn.request(method, endpoint, body)

    response = conn.getresponse()
    if response.status < 200 or response.status >= 300:
        raise SystemZError("{} {}: status {}".format(
            method, endpoint, response.status))

    return response
