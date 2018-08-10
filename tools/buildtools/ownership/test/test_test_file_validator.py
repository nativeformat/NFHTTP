# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

import os
import unittest

from nose.tools import raises

from test_file_validator import TestFileValidator


class TestFileValidatorTest(unittest.TestCase):

    def setUp(self):
        self.fixture_dir = os.path.realpath(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'fixtures', 'test_file_validator'))

    def test_annotate_files_valid(self):
        validator = TestFileValidator(
            test_file_root=os.path.join(self.fixture_dir, 'valid', 'test'),
            src_roots=[os.path.join(self.fixture_dir, 'valid', 'src')])
        errors = validator.validate()
        self.assertIsNone(errors)
        stats = validator.get_stats()
        self.assertDictEqual(stats['owner_count'], {'owner1': 1})
        self.assertEqual(stats['has_feature_count'], 1)
        self.assertEqual(stats['error_count'], 0)
        self.assertEqual(stats['test_file_count'], 2)
        self.assertEqual(stats['tests_with_owner_count'], 1)

    @raises(ValueError)
    def test_annotate_files_src_directory_nonexisting(self):
        TestFileValidator(
            test_file_root=os.path.join(self.fixture_dir, 'valid', 'test'),
            src_roots=[os.path.join(self.fixture_dir, 'doesnotexist')])

    @raises(ValueError)
    def test_annotate_files_test_root_nonexisting(self):
        TestFileValidator(
            test_file_root=os.path.join(self.fixture_dir, 'nonexisting'),
            src_roots=[os.path.join(self.fixture_dir, 'valid', 'src')])

    def test_annotate_files_non_matching_package_src_path(self):
        validator = TestFileValidator(
            test_file_root=os.path.join(self.fixture_dir, 'valid', 'test'),
            src_roots=[os.path.join(self.fixture_dir, 'valid', 'src', 'com')])
        errors = validator.validate()
        self.assertEqual(len(errors), 1)
        file_errors = errors.values()[0]
        self.assertEqual(len(file_errors), 1)
        mesg = file_errors[0]
        self.assertEqual(
            mesg,
            'No src paths found for the package: com.spotify.package1')
        stats = validator.get_stats()
        self.assertDictEqual(stats['owner_count'], {'UNKNOWN': 1})
        self.assertEqual(stats['has_feature_count'], 1)
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(stats['test_file_count'], 2)
        self.assertEqual(stats['tests_with_owner_count'], 0)
