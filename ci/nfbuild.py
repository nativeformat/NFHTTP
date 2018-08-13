#!/usr/bin/env python
'''
 * Copyright (c) 2018 Spotify AB.
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
'''

import filecmp
import fnmatch
import json
import os
import pprint
import signal
import shutil
import subprocess
import sys
import time
import yaml


class NFBuild(object):
    def __init__(self):
        ci_yaml_file = os.path.join('ci', 'ci.yaml')
        self.build_configuration = yaml.load(open(ci_yaml_file, 'r'))
        self.pretty_printer = pprint.PrettyPrinter(indent=4)
        self.current_working_directory = os.getcwd()
        self.build_directory = 'build'
        self.build_type = 'Release'
        self.output_directory = os.path.join(self.build_directory, 'output')
        self.statically_analyzed_files = []

    def build_print(self, print_string):
        print print_string
        sys.stdout.flush()

    def makeBuildDirectory(self):
        if os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)
        os.makedirs(self.build_directory)
        os.makedirs(self.output_directory)

    def installDependencies(self, android=False):
        self.android = android

    def generateProject(self,
                        code_coverage=False,
                        address_sanitizer=False,
                        thread_sanitizer=False,
                        undefined_behaviour_sanitizer=False,
                        ios=False,
                        use_curl=False,
                        android=False,
                        android_arm=False):
        assert True, "generateProject should be overridden by subclass"

    def buildTarget(self, target, sdk='macosx'):
        assert True, "buildTarget should be overridden by subclass"

    def lintCPPFile(self, filepath, make_inline_changes=False):
        current_source = open(filepath, 'r').read()
        clang_format_call = [self.clang_format_binary]
        if make_inline_changes:
            clang_format_call.append('-i')
        clang_format_call.append(filepath)
        new_source = subprocess.check_output(clang_format_call)
        if current_source != new_source and not make_inline_changes:
            self.build_print(
                filepath + " failed C++ lint, file should look like:")
            self.build_print(new_source)
            return False
        return True

    def lintCPPDirectory(self, directory, make_inline_changes=False):
        passed = True
        for root, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if not filename.endswith(('.cpp', '.h', '.m', '.mm')):
                    continue
                full_filepath = os.path.join(root, filename)
                if not self.lintCPPFile(full_filepath, make_inline_changes):
                    passed = False
        return passed

    def lintCPP(self, make_inline_changes=False):
        lint_result = self.lintCPPDirectory('source', make_inline_changes)
        lint_result &= self.lintCPPDirectory('include', make_inline_changes)
        if not lint_result:
            sys.exit(1)

    def lintCmakeFile(self, filepath):
        self.build_print("Linting: " + filepath)
        return subprocess.call(['cmakelint', filepath]) == 0

    def lintCmakeDirectory(self, directory):
        passed = True
        for root, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if not filename.endswith('CMakeLists.txt'):
                    continue
                full_filepath = os.path.join(root, filename)
                if not self.lintCmakeFile(full_filepath):
                    passed = False
        return passed

    def lintCmake(self):
        lint_result = self.lintCmakeFile('CMakeLists.txt')
        lint_result &= self.lintCmakeDirectory('source')
        if not lint_result:
            sys.exit(1)

    def staticallyAnalyse(self, target, include_regex=None):
        assert True, "staticallyAnalyse should be overridden by subclass"

    def buildGradle(self):
        exit_code = subprocess.call(['./gradlew', 'assemble'])
        if exit_code != 0:
            sys.exit(exit_code)

    def packageArtifacts(self):
        assert True, "packageArtifacts should be overridden by subclass"

    def make_archive(self, source, destination):
        base = os.path.basename(destination)
        name = base.split('.')[0]
        format = base.split('.')[1]
        archive_from = os.path.dirname(source)
        archive_to = os.path.basename(source.strip(os.sep))
        print(source, destination, archive_from, archive_to)
        shutil.make_archive(name, format, archive_from, archive_to)
        shutil.move('%s.%s'%(name,format), destination)

    def find_file(self, directory, file_name, multiple_files=False):
        matches = []
        for root, dirnames, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, file_name):
                matches.append(os.path.join(root, filename))
                if not multiple_files:
                    break
            if not multiple_files and len(matches) > 0:
                break
        return matches

    def runIntegrationTests(self):
        # Build the CLI target
        cli_target_name = 'NFHTTPCLI'
        cli_binary = self.targetBinary(cli_target_name)
        self.buildTarget(cli_target_name)
        # Launch the dummy server
        root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        cwd = os.path.join(os.path.join(root_path, 'resources'), 'localhost')
        cmd = 'python -m SimpleHTTPServer 6582'
        pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, preexec_fn=os.setsid, cwd=cwd, shell=True)
        time.sleep(3)
        cli_result = self.runIntegrationTestsUnderDummyServer(cli_binary, root_path)
        os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
        if cli_result:
            sys.exit(cli_result)

    def runIntegrationTestsUnderDummyServer(self, cli_binary, root_path):
        output_responses = os.path.join(root_path, 'responses')
        resources_path = os.path.join(root_path, 'resources')
        for integration_test in self.build_configuration['integration_tests']:
            if os.path.exists(output_responses):
                shutil.rmtree(output_responses)
            os.makedirs(output_responses)
            requests = integration_test['requests']
            self.build_print("Running Integration Test: " + requests)
            cli_result = subprocess.call([cli_binary, '-i', os.path.join(root_path, requests), '-o', output_responses])
            if cli_result:
                return cli_result
            expected_responses = integration_test['responses']
            expected_responses_json = json.load(open(expected_responses))
            actual_responses = os.path.join(output_responses, 'responses.json')
            actual_responses_json = json.load(open(actual_responses))
            requests_json = json.load(open(requests))
            for request in requests_json['requests']:
                request_id = request['id']
                expected_response = expected_responses_json['responses'][request_id]
                actual_response = actual_responses_json['responses'][request_id]
                if not self.checkResponses(expected_response, actual_response, resources_path, integration_test):
                    return 1
            self.build_print("Integration Test Passed")
        return 0

    def checkResponses(self, expected_response, actual_response, resources_path, integration_test):
        if not filecmp.cmp(os.path.join(resources_path, expected_response['payload']), actual_response['payload']):
            self.build_print("ERROR: Integration Test " + integration_test['requests'] + " failed")
            self.build_print("Payloads do not match")
            return False
        return True

    def targetBinary(self, target):
        for root, dirnames, filenames in os.walk(self.build_directory):
            for filename in fnmatch.filter(filenames, target):
                full_target_file = os.path.join(root, filename)
                return full_target_file
        return ''

    def collectCodeCoverage(self):
        for root, dirnames, filenames in os.walk('build'):
            for filename in fnmatch.filter(filenames, '*.gcda'):
                full_filepath = os.path.join(root, filename)
                if full_filepath.startswith('build/source/') and \
                   '/tests/' not in full_filepath:
                    continue
                os.remove(full_filepath)
        llvm_run_script = os.path.join(
            os.path.join(
                self.current_working_directory,
                'ci'),
            'llvm-run.sh')
        cov_info = os.path.join('build', 'cov.info')
        lcov_result = subprocess.call([
            self.lcov_binary,
            '--directory',
            '.',
            '--base-directory',
            '.',
            '--gcov-tool',
            llvm_run_script,
            '--capture',
            '-o',
            cov_info])
        if lcov_result:
            sys.exit(lcov_result)
        coverage_output = os.path.join(self.output_directory, 'code_coverage')
        genhtml_result = subprocess.call([
            self.genhtml_binary,
            cov_info,
            '-o',
            coverage_output])
        if genhtml_result:
            sys.exit(genhtml_result)
