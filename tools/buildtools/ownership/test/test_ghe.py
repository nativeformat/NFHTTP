import mock
import os
import subprocess
import unittest

import ghe

from ghe import GheError

from ghe import commit_file
from ghe import push_to_origin
from ghe import add_file
from ghe import build_message
from ghe import is_file_changed
from ghe import create_commit
from ghe import exec_git_command
from ghe import build_config_options
from ghe import read_gitconfig


class GheTest(unittest.TestCase):

    def setUp(self):
        self.mock_subprocess_responses = {}

        def mock_check_output(*args, **kwargs):
            args = " ".join(args[0])
            return self.mock_subprocess_responses.get(args)

        subprocess.check_output = mock.Mock()
        subprocess.check_output.side_effect = mock_check_output
        subprocess.check_call = mock.Mock()

    def test_push_to_origin(self):
        gitconfig = {'remote':
                    {'origin':
                    {'url': 'git@ghe.spotify.net:origin-owner/project.git'}}}
        target_branch = "master"

        push_to_origin(gitconfig, target_branch)
        subprocess.check_output.assert_called_with(
            ['git', 'push',
                gitconfig['remote']['origin']['url'],
                "HEAD:%s" % target_branch], stderr=subprocess.STDOUT)

    def test_push_to_origin_with_no_origin(self):
        with self.assertRaises(ValueError):
            push_to_origin({}, "master")

    def test_push_to_origin_with_rejection(self):
        url = 'git@ghe.spotify.net'
        target_branch = 'master'
        gitconfig = {'remote': {'origin': {
            'url': "%s:origin-owner/project.git" % url}}}

        def mock_check_output_exception(*args, **kwargs):
            raise subprocess.CalledProcessError(
                1,
                "git push %s HEAD:%s" % (url, target_branch),
                "! [rejected] HEAD -> %s (non-fast-forward)" % target_branch)
        subprocess.check_output.side_effect = mock_check_output_exception

        with self.assertRaises(GheError):
            push_to_origin(gitconfig, target_branch)

    def test_add_file(self):
        file_path = "file_path"

        add_file(file_path)
        subprocess.check_call.assert_called_with(
            ['git', 'add', file_path])

    def test_build_message(self):
        file_path = "file_path"

        self.mock_subprocess_responses[
            "git diff-index HEAD %s" % file_path
        ] = ':100644 100644 1c2e7e716ed8cb0b1b3769e4caf2f3081ce208ea ' \
            '94271c91080ef38ca08142b7a3eb7178ff876b75 M file_path'

        self.assertTrue(len(build_message(file_path)) > 0)

        self.mock_subprocess_responses[
            "git diff-index HEAD %s" % file_path
        ] = ''
        self.assertFalse(build_message(file_path))

    def test_is_file_changed(self):
        file_path = "file_path"
        self.mock_subprocess_responses[
            "git diff-index HEAD %s" % file_path
        ] = ':100644 100644 1c2e7e716ed8cb0b1b3769e4caf2f3081ce208ea ' \
            '94271c91080ef38ca08142b7a3eb7178ff876b75 M file_path'

        self.assertTrue(is_file_changed(file_path))

        self.mock_subprocess_responses[
            "git diff-index HEAD %s" % file_path
        ] = ''
        self.assertFalse(is_file_changed(file_path))

    def test_create_commit(self):
        message = "test commit message"

        with mock.patch.dict(os.environ, {}, True):
            create_commit(message)
            subprocess.check_call.assert_called_with(
                ['git', 'commit', '', '-m', message])

            create_commit(message, key_one='value1')
            subprocess.check_call.assert_called_with(
                ['git', '-c', 'key_one=value1', 'commit', '', '-m', message])

        with mock.patch.dict(os.environ, {'TEAMCITY_VERSION': '1'}, True):
            create_commit(message)
            subprocess.check_call.assert_called_with(
                ['git', 'commit',
                    '--author="TeamCity <teamcity@spotify.com>"',
                    '-m', message])

    def test_exec_git_command(self):
        exec_git_command('commit')
        subprocess.check_call.assert_called_with(
            ['git', 'commit'])

        exec_git_command('commit', '-m', 'commit message')
        subprocess.check_call.assert_called_with(
            ['git', 'commit', '-m', 'commit message'])

        exec_git_command('commit', '-m', 'commit message',
                         conf_key='conf_value')
        subprocess.check_call.assert_called_with(
            ['git', '-c', 'conf_key=conf_value',
             'commit', '-m', 'commit message'])

    def test_build_config_options(self):
        self.assertEquals([], build_config_options())

        self.assertEquals(['-c', 'key_one=value1'],
                          build_config_options(key_one='value1'))

        self.assertEquals(['-c', 'key_two=value2', '-c', 'key_one=value1'],
                          build_config_options(key_one='value1',
                                               key_two='value2'))

    def test_read_gitconfig(self):
        gitconfig_file = "mock_gitconfig_file"
        self.mock_subprocess_responses[
            "git config --file %s --list" % gitconfig_file
        ] = self.read_file("gitconfig_list")

        gitconfig = read_gitconfig(gitconfig_file)

        self.assertEqual(
            "git@ghe.spotify.net:origin-owner/project.git",
            gitconfig['remote']['origin']['url'])

    def test_commit_file(self):
        ghe.add_file = mock.Mock()
        ghe.build_message = mock.Mock()
        ghe.create_commit = mock.Mock()
        ghe.push_to_origin = mock.Mock()
        ghe.read_gitconfig = mock.Mock()

        ghe.build_message.return_value = ''
        with self.assertRaises(GheError):
            self.assertFalse(commit_file("master", "file"))

        ghe.build_message.return_value = 'mock message'
        commit_file("master", "file")

    def read_file(self, file_name):
        with open(self.fixture("ghe/%s" % file_name), mode="r") as stream:
            return stream.read()

    def fixture(self, path):
        return os.path.join(os.path.dirname(__file__), 'fixtures', path)
