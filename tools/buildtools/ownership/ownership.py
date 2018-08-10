#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016-2017 Spotify AB

from argparse import ArgumentParser
import json
import logging
import os
import sys

from ghe import commit_file
from ghe import GheError
from git_diff import GitDiff
from mention_bot import write_mentionbot_with_service_info_files
from service_info import ServiceInfo
from system_z import synchronize_system_z
from test_file_validator import TestFileValidator


class OwnershipCLI(object):

    def __init__(self, argv):
        parser = ArgumentParser(
            description='Perform ownership-related tasks.',
            usage='''%s

Subcommands:
  validate:     lint and validate service-info.yaml files.
  list:         list service-info.yaml files.
  mentionbot:   update mentionbot config with service-info.yaml files.
  commit:       commit mentionbot config to ghe.
  synchronize:  synchronize repo with system-z.
  testmapper:   find owners for test files using content heuristics.
  gitdiffcheck: check that touched source files are properly owned
  dump:         create json dump of service-info.yaml files and their contents

''' % (os.path.basename(__file__))
        )

        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(argv[1:2])

        if not hasattr(self, args.command):
            print 'Unrecognized command'
            parser.print_help()
            exit(1)

        getattr(self, args.command)(argv[2:])

    ###########################################################################

    def validate(self, args):
        parser = self._subparser('Validates service-info files.')
        parser.add_argument(
            '--squads',
            action='store_true',
            help='Validate squads against system-z')
        parser.add_argument(
            '--features',
            action='store',
            help='Comma-separated list of features to check against '
                 'feature_test fields.  This tool will validate that '
                 'all features have been found in service-info files')

        options = parser.parse_args(args)
        os.chdir(options.root)

        check_features = []
        if options.features:
            check_features = options.features.split(',')

        paths = ServiceInfo.scan_git_from_pwd(options.exclude)
        malformed = ServiceInfo.validate_files(
            paths, options.squads, check_features)
        if len(malformed) > 0:
            self._print_file_errors(malformed)
            exit(1)

    def testmapper(self, args):
        parser = self._subparser('Finds owners for test files.')
        parser.add_argument(
            '--test-root',
            action='store',
            required=True,
            help='Validates test files in test root against ownership')
        parser.add_argument(
            '--src-roots',
            action='store',
            required=True,
            help='Comma-separated paths containing base roots for code related'
                 ' to test files')
        parser.add_argument(
            '--test-file-pattern',
            action='store',
            help='Glob pattern for matching test files')
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Print detailed errors and exit 1 if any errors exist')
        parser.add_argument(
            '--format',
            action='store',
            default='stats',
            help='Output format: "stats" or "packagemap"')

        options = parser.parse_args(args)
        validator = TestFileValidator(
            options.test_root,
            options.test_file_pattern,
            options.src_roots.split(','))
        errors = validator.validate()
        if options.format == 'stats':
            print json.dumps(validator.get_stats(), indent=4)
        else:
            print json.dumps(validator.get_package_owner(), indent=4)
        if options.validate and errors:
            self._print_file_errors(errors, options.teamcity)
            exit(1)

    ###########################################################################

    def list(self, args):
        parser = self._subparser('Lists service-info files.')
        options = parser.parse_args(args)
        os.chdir(options.root)

        paths = ServiceInfo.scan_git_from_pwd(options.exclude)
        for path in paths:
            print(path)

    ###########################################################################

    def mentionbot(self, args):
        parser = self._subparser(('Updates mentionbot file with data extracted'
                                  ' from service-info files.'))

        options = parser.parse_args(args)
        os.chdir(options.root)

        paths = ServiceInfo.scan_git_from_pwd(options.exclude)
        write_mentionbot_with_service_info_files(paths)

    ###########################################################################

    def commit(self, args):
        parser = self._subparser(('Commit .mention-bot file to ghe'))
        parser.add_argument(
            '-b', '--branch',
            action="store",
            help='Target branch to commit mentionbot file to.',
            default='master')

        parser.add_argument(
            '-n', '--name',
            action="store",
            help='user.name git config value',
            default='TeamCity')

        parser.add_argument(
            '-e', '--email',
            action="store",
            help='user.email git config value',
            default='teamcity@spotify.com')

        options = parser.parse_args(args)
        os.chdir(options.root)

        try:
            commit_file(options.branch, '.mention-bot', **{
                'user.name': options.name,
                'user.email': options.email})
        except GheError, e:
            print "[ghe-error] %s" % e
            exit(1)

    ###########################################################################

    def synchronize(self, args):
        parser = ArgumentParser(description=('Synchronizes the given repo with'
                                             'System-Z using sysmodel.'))
        parser.add_argument(
            '-r', '--repo',
            action="store",
            help='The GHE repo name.',
            required=True)

        options = parser.parse_args(args)
        success = synchronize_system_z(options.repo)
        if not success:
            exit(1)

    def gitdiffcheck(self, args):
        parser = self._subparser(
            'Checks git-diff files for ownership properties')
        parser.add_argument(
            '-b', '--base',
            action='store',
            default='refs/heads/master',
            help='The base commit to compare against')
        parser.add_argument(
            '-c', '--commit',
            action='store',
            default='HEAD',
            help='The commit to compare against the base')
        parser.add_argument(
            '-s', '--src-roots',
            action='store',
            required=True,
            help='A comma-separated list of paths indicating which sources'
                 ' should map to a service-info.yaml file.')
        parser.add_argument(
            '-m', '--file-match',
            action='store',
            default='.*',
            help='Regex to match against src files')
        parser.add_argument(
            '--override-tag',
            default='nocheckowner',
            help='Tag to put on one of the commit messages to skip this check')

        options = parser.parse_args(args)
        logger = make_logger(options.verbose)

        src_roots = map(os.path.realpath, options.src_roots.split(','))

        diff = GitDiff(options.base, options.commit, options.file_match)
        for (commit, message) in diff.commit_messages():
            logger.debug("Checking commit={}, message={}".format(
                commit, message))
            if options.override_tag in message:
                print ("Found override message '{}' in commit {}, "
                       "skipping ownership check").format(
                               options.override_tag,
                               commit,
                               message)
                exit(0)

        errors = []
        check_files = filter(lambda df: df.status in ('M', 'A'), diff.files())
        for diff_file in check_files:
            full_path = os.path.realpath(diff_file.path)
            valid_sources = filter(lambda pth: pth in full_path, src_roots)
            logger.debug(
                "Checking diff file path={} against matching roots={}".format(
                    full_path, valid_sources))
            if len(valid_sources) > 0:
                src_path = valid_sources[0]
                service_info = ServiceInfo.find_relative_to_path(
                    full_path, src_path)
                if service_info:
                    logger.debug(
                        'Found ownership for path={}, service_info={}'.format(
                            full_path,
                            service_info.file_path))
                else:
                    errors.append(
                        'Could not find service-info.yaml file'
                        ' for path: {}'.format(full_path))
        if len(errors) > 0:
            for error in errors:
                self._print_error(error, teamcity=options.teamcity)

            tag_type = 'phrase' if ' ' in options.override_tag else 'word'
            self._print_error(
                ('Ownership check failed.  Include the {} "{}" in one'
                 ' of your commit messages to skip this check.').format(
                    tag_type,
                    options.override_tag),
                teamcity=options.teamcity)
            exit(1)

    def dump(self, args):
        parser = self._subparser(
            'Create json dump of service-info.yaml files in repo '
            'and their contents')
        parser.add_argument(
            '--dump-to-file',
            action='store',
            default='service-infos.json',
            help='Name of file to dump all service-info.yaml data')
        options = parser.parse_args(args)
        os.chdir(options.root)
        service_infos_dict = ServiceInfo.load_service_infos(options.exclude)
        with open(options.dump_to_file, mode='w') as output_file:
            json.dump(service_infos_dict, output_file)
        exit(0)

    ###########################################################################

    def _tc_escape(self, msg):
        esc = {
            "'": "|'", "|": "||", "\n": "|n", "\r": "|r", "[": "|[", "]": "|]"
        }
        return "".join([esc.get(x, x) for x in msg])

    def _subparser(self, desc):
        parser = ArgumentParser(description=desc)
        parser.add_argument(
            '-r', '--root',
            action="store",
            help='Path to the root source folder.',
            default='.')
        parser.add_argument(
            '-x', '--exclude',
            nargs='*',
            action="store",
            help='Path to exclude from scan (optional).',
            default=[])
        parser.add_argument(
            '--teamcity',
            action='store_true',
            help='Output errors as TeamCity problems.')
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print debug-level log messages.')

        return parser

    def _print_error(self, message, teamcity=False):
        if teamcity:
            print("##teamcity[buildProblem description='{}']".format(
                self._tc_escape(message)))
        else:
            sys.stderr.write("{}{}".format(message, os.linesep))

    def _print_file_errors(self, file_errors, teamcity=False):
        for path, errors in file_errors.items():
            if teamcity:
                for value in errors:
                    mesg = 'ownership: {} ({})'.format(value, path)
                    self._print_error(mesg, teamcity=True)
            else:
                self._print_error("Errors found in {}:".format(path))
                for value in errors:
                    self._print_error("    {}".format(value))


def make_logger(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=log_level, format=log_format)
    return logging.getLogger(__name__)

if __name__ == '__main__':
    OwnershipCLI(sys.argv)
