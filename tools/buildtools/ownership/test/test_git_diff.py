# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

import os
import subprocess
import unittest

import git_diff


class SubprocessMock():
    calls = []
    return_value = ''

    def check_output(self, cmd, shell=False):
        self.calls.append([cmd, shell])
        return self.return_value


class GitDiffTest(unittest.TestCase):

    def setUp(self):
        git_diff.subprocess = SubprocessMock()

    def tearDown(self):
        git_diff.subprocess = subprocess

    def test_files_listing(self):
        diff = git_diff.GitDiff('HEAD', 'refs/heads/master', r'.*\.py$')
        git_diff.subprocess.return_value = 'A ownership.py' + os.linesep + 'M service_info.py' + os.linesep # NOQA
        files = diff.files()
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].status, 'A')
        self.assertTrue(os.sep.join(['ownership', 'ownership.py']) in files[0].path) # NOQA
        self.assertEqual(files[1].status, 'M')

    def test_files_no_match(self):
        diff = git_diff.GitDiff('HEAD', 'refs/heads/master', r'.*\.java$')
        git_diff.subprocess.return_value = 'A ownership.py' + os.linesep + 'M service_info.py' + os.linesep # NOQA
        files = diff.files()
        self.assertEqual(len(files), 0)

    def test_commit_messages(self):
        diff = git_diff.GitDiff('HEAD', 'refs/heads/master')
        git_diff.subprocess.return_value = os.linesep.join(['commit 7a75b50970d5c8688474cd3f62c7a0769c4ed047', 'Ownership check', 'commit 63f6b83197e4dd2a38022514eead1354ed84ad0e', 'test', 'file-package-mapping']) + os.linesep # NOQA
        cms = diff.commit_messages()
        self.assertEqual(len(cms), 2)
        self.assertEqual(cms[0].sha, '7a75b50970d5c8688474cd3f62c7a0769c4ed047') # NOQA
        self.assertEqual(cms[0].message, 'Ownership check' + os.linesep)
        self.assertEqual(cms[1].sha, '63f6b83197e4dd2a38022514eead1354ed84ad0e') # NOQA
        self.assertEqual(cms[1].message, 'test' + os.linesep + 'file-package-mapping' + os.linesep) # NOQA

