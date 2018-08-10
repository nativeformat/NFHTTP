# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

import fnmatch
import os
import re

from service_info import ServiceInfo


class TestFileValidator:
    def __init__(
            self,
            test_file_root,
            filename_pattern=None,
            src_roots=[]):
        self.file_root = self._find_path(test_file_root)
        self.filename_pattern = filename_pattern
        self.src_roots = []
        for root in src_roots:
            self.src_roots.append(self._find_path(root))

    def _find_path(self, path):
        if os.path.isdir(path):
            return os.path.realpath(path)
        path = os.path.realpath(os.path.join(os.getcwd(), path))
        if os.path.isdir(path):
            return path
        raise ValueError("path not found: {}".format(path))

    def file_matches(self, filename):
        if not self.filename_pattern:
            return True
        return fnmatch.fnmatch(filename, self.filename_pattern)

    def validate(self):
        self._errors = {}
        self._owner_count = {}
        self._package_owner = {}
        self._error_count = 0
        self._package_error_count = 0
        self._src_path_error_count = 0
        self._service_info_error_count = 0
        self._test_file_count = 0
        self._has_feature_count = 0
        self._files_with_owner_count = 0
        self._tests_with_owner_count = 0
        self._tests_with_error_count = 0
        for (path, dirnames, filenames) in os.walk(self.file_root):
            matching = filter(self.file_matches, filenames)
            for path in map(file_prefix(path), matching):
                self.validate_file(path)
        if len(self._errors) > 0:
            return self._errors
        return None

    def get_stats(self):
        return {
            "error_count": self._error_count,
            "owner_count": self._owner_count,
            "test_file_count": self._test_file_count,
            "has_feature_count": self._has_feature_count,
            "package_error_count": self._package_error_count,
            "src_path_error_count": self._src_path_error_count,
            "files_with_owner_count": self._files_with_owner_count,
            "tests_with_owner_count": self._tests_with_owner_count,
            "tests_with_error_count": self._tests_with_error_count,
            "service_info_error_count": self._service_info_error_count
        }

    def get_package_owner(self):
        return self._package_owner

    def validate_file(self, filepath):
        errors = []
        owner = None
        if filepath.endswith('.java'):
            (num_tests, has_feature_annotation, package) = \
                self.get_java_info(filepath)
            if num_tests == 0:
                # It's not a test file, no need to check
                return
            self._test_file_count += 1
            if has_feature_annotation:
                self._has_feature_count += 1
                # We can use feature to map to owner, no need to use package
                return
            if package:
                (owner, error) = self.owner_for_java_package(package)
                if not owner and not error:
                    error = 'No owner found'
                if error:
                    errors.append(error)
                    self._tests_with_error_count += num_tests
                else:
                    self._files_with_owner_count += 1
                    self._tests_with_owner_count += num_tests
                    self._package_owner[package] = owner
            else:
                errors.append('No java package found')
                self._package_error_count += 1
        else:
            return
        increment_dict(self._owner_count, owner if owner else 'UNKNOWN')
        if len(errors) > 0:
            self._error_count += len(errors)
            self._errors[filepath] = errors

    def get_java_info(self, filepath):
        package = None
        num_tests = 0
        has_feature_annotation = False
        with open(filepath, 'r') as fh:
            for line in fh:
                if line.startswith('package'):
                    comps = re.split(r'\s+|;', line)
                    if len(comps) > 1:
                        package = comps[1]
                if '@Feature' in line:
                    has_feature_annotation = True
                if '@Test' in line:
                    num_tests += 1
        return (num_tests, has_feature_annotation, package)

    def owner_for_java_package(self, package):
        relative_path = package.replace('.', os.sep)
        paths_checked = []
        for root in self.src_roots:
            path_check = os.path.join(root, relative_path)
            if os.path.isdir(path_check):
                paths_checked.append(path_check)

                service_info = ServiceInfo.find_relative_to_path(
                        path_check, root)
                if service_info and service_info.owner:
                    return (service_info.owner, None)
        if len(paths_checked) == 0:
            self._src_path_error_count += 1
            return (None, "No src paths found for the package: " + package)
        self._service_info_error_count += 1
        return (None, "No service-info.yaml files found in src"
                      " paths: {}".format(', '.join(paths_checked)))


def increment_dict(dictionary, key):
    if key not in dictionary:
        dictionary[key] = 0
    dictionary[key] += 1


def file_prefix(filepath):
    return lambda fn: os.path.join(filepath, fn)
