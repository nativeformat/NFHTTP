#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016 Spotify AB

# Parse and validate service-info.yaml files
# https://confluence.spotify.net/display/SYS/Defining+Components+Using+YAML

import json
import re
import subprocess
import urllib2
import os
import yaml

COVERAGE_RE = re.compile(r'^\d+%$')
COVERAGE_PATTERN_RE = re.compile(r'(\S+)\s+(\d+%)$')


class ServiceInfo(object):
    SQUADS_URL = 'http://squab.services.system-z.spotify.net/v1/squads'

    @staticmethod
    def scan_git_from_pwd(excludes=None):
        paths = []
        out = subprocess.check_output("git ls-files", shell=True)
        excl_re = None
        if excludes and len(excludes) > 0:
            excl_re = re.compile('^(%s)' % ('|'.join(excludes)))

        for line in out.splitlines():
            if line.endswith('service-info.yaml'):
                if not (excl_re and excl_re.match(line)):
                    paths.append(line)
        return paths

    @staticmethod
    def from_yaml_file(path, raise_on_validation_error=True, squad_list=None):
        value = None
        with open(path, mode='r') as stream:
            value = yaml.load(stream)
        return ServiceInfo(value, raise_on_validation_error, squad_list, path)

    @staticmethod
    def load_yaml_file(path):
        with open(path, mode='r') as stream:
            value = yaml.load(stream)
        return value

    @staticmethod
    def load_service_infos(exclude=None):
        paths = ServiceInfo.scan_git_from_pwd(exclude)
        service_infos_dict = dict()
        for path in paths:
            service_info_dict = ServiceInfo.load_yaml_file(path)
            if service_info_dict:
                dir_path = os.path.dirname(path)
                service_infos_dict[dir_path] = service_info_dict
        return service_infos_dict

    @staticmethod
    def validate_files(paths, validate_squads=False, check_features=[]):
        output = {}

        # download squad list (fail silently)
        squads = None
        if validate_squads:
            try:
                squads = ServiceInfo.fetch_squad_list()
            except:
                pass

        feature_owner_path = {}
        # validate files
        for path in paths:
            obj = ServiceInfo.from_yaml_file(path, False, squads)
            if len(obj.errors) > 0:
                output[path] = obj.errors
            elif len(obj.feature_test) > 0:
                for feature in obj.feature_test:
                    if feature in feature_owner_path:
                        existing_owner, existing_path = \
                            feature_owner_path[feature]
                        if obj.owner != existing_owner:
                            output[path] = [
                                'Feature "{}" with owner "{}" already has '
                                'an owner "{}" at path: {}'
                                .format(
                                    feature,
                                    obj.owner,
                                    existing_owner,
                                    existing_path
                                )
                            ]
                    else:
                        feature_owner_path[feature] = (obj.owner, path)

        if len(check_features) > 0:
            found_features = set(feature_owner_path.keys())
            missing_features = set(check_features).difference(found_features)
            if len(missing_features) > 0:
                tpl = 'Test features not found in service-info files: {}\n' \
                        'Found features: {}'
                output['<project root>'] = [tpl.format(
                    ','.join(missing_features),
                    ','.join(found_features))]
        return output

    @staticmethod
    def fetch_squad_list():
        resp = urllib2.urlopen(ServiceInfo.SQUADS_URL)
        code = resp.getcode()
        if code >= 200 or code < 300:
            data = json.load(resp)
            if isinstance(data, list):
                return data
            raise ValueError('squab: unexpected response')
        raise ValueError('squab: returned {}'.format(code))

    @staticmethod
    def find_relative_to_path(search_path, stop_path=None):
        '''
        Finds a service-info.yaml file relative to the given file path,
        stopping the search at the given source root (non-inclusive) if
        provided.

        Args:
            search_path (str): The path to the file for which you want to
                find an owner.
            stop_path (str): The base path which should end the search.
                If not provided, the search will stop at the file
                system root.

        Returns:
            ServiceInfo: A ServiceInfo object if an owner is found,
                otherwise None
        '''
        if stop_path:
            stop_path = os.path.realpath(stop_path)
        search_path = os.path.realpath(search_path)
        check_path = search_path
        if os.path.isfile(check_path):
            check_path = os.path.dirname(check_path)
        last_path = None
        while check_path \
                and check_path != last_path \
                and check_path != stop_path:
            si_file = os.path.join(check_path, 'service-info.yaml')
            if os.path.isfile(si_file):
                return ServiceInfo.from_yaml_file(
                    si_file,
                    raise_on_validation_error=False)
            last_path = check_path
            check_path = os.path.realpath(os.path.join(check_path, '..'))
        return None

    def __init__(
            self, d,
            raise_on_validation_error=True, squad_list=None, file_path=None):
        # initialize instance vars
        self.file_path = os.path.realpath(file_path) if file_path else None
        self.id = None
        self.description = None
        self.system = None
        self.owner = None
        self.dependencies = []
        self.is_public = False
        self.facts = {}
        self.maintainers = []
        self.service_discovery = []
        self.docs = []
        self.role = []
        self.tags = []
        self.feature_test = []
        self.slack_channel = None
        self.component_type = None
        self.pagerdutykey = None
        self.max_hosts_per_rack = 1
        self.mentionbot_users = []
        self.mentionbot_paths = []

        self.errors = []
        self.raise_on_validation_error = raise_on_validation_error
        self._all_files = None

        if not isinstance(d, dict):
            self._error('ServiceInfo expects a dict')
        else:
            # Required parameters
            self.id = self._get(d, 'id', basestring, True)
            self.description = self._get(d, 'description', basestring, True)
            self.system = self._get(d, 'system', basestring, True)
            self.owner = self._get(d, 'owner', basestring, True)
            self.dependencies = self._getlist(
                d, 'dependencies', basestring, True)

            vis = self._get(d, 'visibility', basestring, True)
            if vis == 'public':
                self.is_public = True
            elif vis == 'private':
                self.is_public = False
            else:
                self._error('visibility must be "private" or "public"')

            # Optional parameters
            f = self._get(d, 'facts', dict, False, {})
            if f:
                self.facts = f
                self.maintainers = self._getlist(
                    f, 'maintainers', basestring, False, False)
                self.service_discovery = self._getlist(
                    f, 'service_discovery', basestring, False, False)
                self.docs = self._getlist(f, 'docs', basestring, False, True)
                self.feature_test = self._getlist(
                    f, 'feature_test', basestring, required=False, wrap=True)
                self.role = self._getlist(f, 'role', basestring, False, True)
                self.tags = self._getlist(f, 'tags', basestring, False, True)

                self.slack_channel = self._get(
                    f, 'slack_channel', basestring, False)
                self.component_type = self._get(
                    f, 'component_type', basestring, False)
                self.pagerdutykey = self._get(
                    f, 'pagerdutykey', basestring, False)
                self.max_hosts_per_rack = self._get(
                    f, 'max_hosts_per_rack', (int, long), False, 1)

                # mentionbot (nyc-infra)
                mb = self._get(f, 'mentionbot', dict, False)
                if mb:
                    self.mentionbot_users = self._getlist(
                        mb, 'users', basestring, True, True)
                    self.mentionbot_paths = self._getlist(
                        mb, 'paths', basestring, False, True)
                diff_cover = self._get(
                    f, 'diff_cover_requirements', dict, False)
                if diff_cover:
                    for (key, conf) in diff_cover.iteritems():
                        self._validate_diff_cover_requirements(key, conf)

        # validate squad
        if squad_list and self.owner not in squad_list:
            self._error('{} is not a valid squad'.format(self.owner))

    def _validate_diff_cover_requirements(self, key, conf):
        def err(mesg):
            self._error(
                "Error in diff-cover requirements for key={}, {}"
                .format(key, mesg))
        if not self._check_type('diff-cover config', conf, dict, err):
            return
        if 'coverage' in conf:
            self._check_regex('coverage', conf['coverage'], COVERAGE_RE, err)
        if 'strict' in conf:
            self._check_type('strict', conf['strict'], bool, err)
        if 'patterns' in conf and self._check_type(
                'patterns', conf['patterns'], list, err):
            for pattern in conf['patterns']:
                if self._check_regex(
                        'coverage-pattern', pattern, COVERAGE_PATTERN_RE, err):
                    match_results = COVERAGE_PATTERN_RE.match(pattern)
                    glob, percent = match_results.group(1, 2)
                    self._check_regex(
                        'pattern-coverage', percent, COVERAGE_RE, err)
                    self._check_glob_matches_files('pattern-glob', glob, err)

    # get the given fact
    def get_fact(self, fact, fallback=None):
        return self.facts.get(fact, fallback)

    def find_file(self, relative_to_file, stop_path=None):
        return None

    # handle validation errors
    def _error(self, val):
        if self.raise_on_validation_error:
            raise ValueError(val)
        else:
            self.errors.append(val)

    def _check_regex(self, name, val, regex, error_fn=None):
        if not error_fn:
            error_fn = self._error
        if not self._check_type(name, val, str):
            return False
        if not regex.match(val):
            error_fn("{} ({}) must match regex={}".format(
                name, val, regex.pattern))
            return False
        return True

    def _check_type(self, name, val, type_check, error_fn=None):
        if not error_fn:
            error_fn = self._error
        if type(val) is not type_check:
            error_fn("{} must be a {}, is instead a {} (value={})".format(
                    name, type_check, type(val), val))
            return False
        return True

    def _check_glob_matches_files(self, name, pattern, error_fn=None):
        if not self.file_path:
            return True
        if not error_fn:
            error_fn = self._error
        base_path = os.path.dirname(self.file_path)
        regex = re.compile(pattern.replace('**', '[recursive-match]')
                                  .replace('*', '[^/].*')
                                  .replace('[recursive-match]', '.*'))
        for relpath in self._get_all_files():
            if regex.match(relpath):
                return True
        error_fn("pattern ({}) does not match any files in basedir: {}"
                 .format(pattern, base_path))
        return False

    def _get_all_files(self):
        if self._all_files:
            return self._all_files
        self._all_files = []
        base_path = os.path.dirname(self.file_path)
        for (root, dirnames, filenames) in os.walk(base_path):
            for filename in filenames:
                abspath = os.path.join(root, filename)
                relpath = os.path.relpath(abspath, base_path)
                self._all_files.append(self._normalize_path(relpath))
        return self._all_files

    @staticmethod
    def _normalize_path(path):
        return path.replace(os.path.sep, '/')

    # get a value of the given type from the supplied dict
    def _get(self, d, key, typ, required=False, default=None):
        value = d.get(key, None)
        if value is None:
            if required:
                self._error('%s is required' % (key))
            return default
        if not isinstance(value, typ):
            self._error('%s must be a %s' % (key, typ.__name__))
            return default
        return value

    # get a list of the given type from the supplied dict
    def _getlist(self, d, key, typ, required=False, wrap=False, default=[]):
        value = d.get(key, None)
        if value is None:
            if required:
                self._error('%s is required' % (key))
                return default
            else:
                value = []

        if not isinstance(value, list):
            if wrap:
                value = [value]
            else:
                self._error('%s must be a list' % (key))
                return default

        for sub in value:
            if not isinstance(sub, typ):
                self._error(
                    '%s must be a list of %s' % (key, typ.__name__))
                break

        return value
