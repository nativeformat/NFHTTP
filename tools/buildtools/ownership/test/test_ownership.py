# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

import unittest

import git_diff
import service_info
import ownership
import mock
import sys


class OwnershipTest(unittest.TestCase):

    def setUp(self):
        self.git_diff = mock.MagicMock()
        ownership.GitDiff = lambda x, y, z: self.git_diff
        ownership.ServiceInfo = mock.MagicMock()
        ownership.sys = mock.MagicMock()

    def tearDown(self):
        ownership.GitDiff = git_diff.GitDiff
        ownership.ServiceInfo = service_info.ServiceInfo
        ownership.sys = sys

    def gitdiffcheck_with_expected_error(self, code):
        exited = False
        try:
            ownership.OwnershipCLI([
                    'script', 'gitdiffcheck',
                    '--src-roots', './test',
                    '--override-tag', 'nocheckowner'])
        except SystemExit as exit_error:
            self.assertEqual(exit_error.message, code)
            exited = True
        if code is None:
            return
        self.assertTrue(exited)

    def test_diffcheck_with_message(self):
        self.git_diff.commit_messages.return_value = [
                git_diff.CommitMessage('sha', 'nocheckowner')]
        self.gitdiffcheck_with_expected_error(0)

    def test_diffcheck_with_no_files(self):
        self.git_diff.commit_messages.return_value = [
                git_diff.CommitMessage('sha', 'some commit')]
        self.git_diff.files.return_value = []
        self.gitdiffcheck_with_expected_error(None)

    def test_diffcheck_with_owned_files(self):
        self.git_diff.commit_messages.return_value = [
                git_diff.CommitMessage('sha', 'some commit')]
        self.git_diff.files.return_value = [
                git_diff.DiffFile('A', 'test/test_ownership.py')]
        ownership.ServiceInfo.find_relative_to_path.return_value \
            = ownership.ServiceInfo()
        self.gitdiffcheck_with_expected_error(None)

    def test_diffcheck_with_unowned_files(self):
        self.git_diff.commit_messages.return_value = [
                git_diff.CommitMessage('sha', 'some commit')]
        self.git_diff.files.return_value = [
                git_diff.DiffFile('A', 'test/test_ownership.py')]
        ownership.ServiceInfo.find_relative_to_path.return_value = False
        self.gitdiffcheck_with_expected_error(1)

    def test_diffcheck_with_message_and_unowned_files(self):
        self.git_diff.commit_messages.return_value = [
                git_diff.CommitMessage('sha', 'nocheckowner')]
        self.git_diff.files.return_value = [
                git_diff.DiffFile('A', 'test/test_ownership.py')]
        ownership.ServiceInfo.find_relative_to_path.return_value = False
        self.gitdiffcheck_with_expected_error(0)
