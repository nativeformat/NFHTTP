# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

import json
import mock
import os
import unittest
from service_info import ServiceInfo


class ServiceInfoTest(unittest.TestCase):

    def fixture(self, path):
        return os.path.join(os.path.dirname(__file__), 'fixtures/service_info', path)

    def test_valid_files_passes(self):
        # Arrange
        files = [self.fixture("valid_service_info_1.yaml"),
                 self.fixture("valid/valid_service_info_2.yaml"),
                 self.fixture("valid/valid_service_info_without_facts.yaml"),
                 self.fixture("valid/valid_service_info_without_mention_bot.yaml")]

        # Act
        malformed = ServiceInfo.validate_files(files)

        # Assert
        self.assertEqual(0, len(malformed))

    def assert_list_contains_matching(self, lst, item):
        matching = filter(lambda x: item in x, lst)
        self.assertTrue(
            len(matching) > 0,
            "Expected list={} to contain string/list matching item={}".format(
                lst, item))

    def test_invalid_file_1_fails(self):
        # Arrange
        invalid_file_name = self.fixture('invalid/invalid_service_info_1.yaml')
        files = [invalid_file_name]

        # Act
        malformed = ServiceInfo.validate_files(files)

        # Assert
        self.assertEqual(1, len(malformed))
        self.assertTrue(invalid_file_name in malformed)
        errors_list = malformed.get(invalid_file_name)
        self.assertIsNotNone(errors_list)
        self.assertEqual(1, len(errors_list))
        self.assertEqual("id is required", errors_list[0])

    def test_invalid_file_2_fails(self):
        # Arrange
        invalid_file_name = self.fixture('invalid/invalid_service_info_2.yaml')
        files = [invalid_file_name]

        # Act
        malformed = ServiceInfo.validate_files(files)

        # Assert
        self.assertEqual(1, len(malformed))
        self.assertTrue(invalid_file_name in malformed)
        errors_list = malformed.get(invalid_file_name)
        self.assertIsNotNone(errors_list)
        self.assertEqual(2, len(errors_list))
        self.assertEqual("description is required", errors_list[0])
        self.assertEqual("dependencies must be a list", errors_list[1])

    def test_invalid_file_3_fails(self):
        # Arrange
        invalid_file_name = self.fixture('invalid/invalid_service_info_3.yaml')
        files = [invalid_file_name]

        # Act
        malformed = ServiceInfo.validate_files(files)

        # Assert
        self.assertEqual(1, len(malformed))
        self.assertTrue(invalid_file_name in malformed)
        errors_list = malformed.get(invalid_file_name)
        self.assertIsNotNone(errors_list)
        self.assertEqual(2, len(errors_list))
        self.assertEqual("dependencies must be a list of basestring", errors_list[0])
        self.assertEqual("facts must be a dict", errors_list[1])

    def test_invalid_file_and_valid_file_fails_only_on_invalid_file(self):
        # Arrange
        valid_file_name = self.fixture('valid/valid_service_info_2.yaml')
        invalid_file_name = self.fixture('invalid/invalid_service_info_1.yaml')
        files = [valid_file_name, invalid_file_name]

        # Act
        malformed = ServiceInfo.validate_files(files)

        # Assert
        self.assertEqual(1, len(malformed))
        self.assertFalse(valid_file_name in malformed)
        self.assertTrue(invalid_file_name in malformed)
        errors_list = malformed.get(invalid_file_name)
        self.assertIsNotNone(errors_list)
        self.assertEqual(1, len(errors_list))
        self.assertEqual("id is required", errors_list[0])

    def test_valid_file_with_diff_cover_passes(self):
        # Arrange
        files = [self.fixture("valid/valid_service_info_with_diff_cover.yaml")]
        malformed = ServiceInfo.validate_files(files)
        print malformed
        self.assertEqual(0, len(malformed))

    def test_diff_cover_fails_on_malformed_content(self):
        # Arrange
        files = [self.fixture("invalid/invalid_diff_cover.yaml")]
        malformed = ServiceInfo.validate_files(files)
        self.assertEqual(1, len(malformed))
        errors_list = malformed.get(files[0])
        self.assertEqual(len(errors_list), 6)
        self.assert_list_contains_matching(
            errors_list,
            "key=integration, coverage (baz) must match")
        self.assert_list_contains_matching(
            errors_list,
            "key=integration, patterns must be a")
        self.assert_list_contains_matching(
            errors_list,
            "key=unit, strict must be a")
        self.assert_list_contains_matching(
            errors_list,
            "key=unit, coverage-pattern")
        self.assert_list_contains_matching(
            errors_list,
            "key=unit, coverage (50%238) must match")
        self.assert_list_contains_matching(
            errors_list,
            "does not match any files")

    @mock.patch("service_info.ServiceInfo.scan_git_from_pwd")  # NOQA
    def test_loading_service_infos(self, scan_got_from_pwd):
        service_info_one = "test_directory/service-info.yaml"
        service_info_two = "test_directory/test_directory_2/service-info.yaml"
        abs_service_info_one = self.fixture(service_info_one)
        abs_service_info_two = self.fixture(service_info_two)

        scan_got_from_pwd.return_value = [
            abs_service_info_one, abs_service_info_two
        ]

        service_infos_dict = ServiceInfo.load_service_infos()
        with open(self.fixture("test_directory/service-infos.json"), 'r') as output:  # NOQA
            service_infos_fixture = json.load(output)
            self.assertEqual(
                service_infos_dict[os.path.dirname(abs_service_info_one)],
                service_infos_fixture[os.path.dirname(service_info_one)])
            self.assertEqual(
                service_infos_dict[os.path.dirname(abs_service_info_two)],
                service_infos_fixture[os.path.dirname(service_info_two)])  # NOQA
