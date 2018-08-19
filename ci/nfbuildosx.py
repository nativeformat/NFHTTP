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

import fnmatch
import os
import plistlib
import re
import shutil
import subprocess
import sys

from distutils import dir_util
from nfbuild import NFBuild


class NFBuildOSX(NFBuild):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.project_file = os.path.join(
            self.build_directory,
            'NFHTTP.xcodeproj')
        self.cmake_binary = 'cmake'
        self.curl_directory = self.current_working_directory + '/libraries/curl'
        self.clang_format_binary = 'clang-format'
        self.android_ndk_folder = '/usr/local/share/android-ndk'
        self.ninja_binary = 'ninja'
        self.ios = False
        self.android = False
        self.android_arm = False

    def generateProject(self,
                        code_coverage=False,
                        address_sanitizer=False,
                        thread_sanitizer=False,
                        undefined_behaviour_sanitizer=False,
                        ios=False,
                        use_curl=False,
                        use_cpprest=False,
                        android=False,
                        android_arm=False,
                        gcc=False):
        self.use_ninja = android or android_arm
        self.android = android
        self.android_arm = android_arm
        cmake_call = [
            self.cmake_binary,
            '..']
        if self.use_ninja:
            cmake_call.append('-GNinja')
        else:
            cmake_call.append('-GXcode')
        if self.build_type == 'Release':
            cmake_call.append('-DCREATE_RELEASE_BUILD=1')
        else:
            cmake_call.append('-DCREATE_RELEASE_BUILD=0')
        if address_sanitizer:
            cmake_call.append('-DUSE_ADDRESS_SANITIZER=1')
        if use_curl:
            cmake_call.append('-DUSE_CURL=1')
        if use_cpprest:
            cmake_call.append('-DUSE_CPPRESTSDK=1')
        if code_coverage:
            cmake_call.append('-DCODE_COVERAGE=1')
        else:
            cmake_call.append('-DCODE_COVERAGE=0')
        if android or android_arm:
            android_abi = 'x86_64'
            android_toolchain_name = 'x86_64-llvm'
            if android_arm:
                android_abi = 'arm64-v8a'
                android_toolchain_name = 'arm64-llvm'
            cmake_call.extend([
                '-DANDROID=1',
                '-DCMAKE_TOOLCHAIN_FILE=' + self.android_ndk_folder + '/build/cmake/android.toolchain.cmake',
                '-DANDROID_NDK=' + self.android_ndk_folder,
                '-DANDROID_ABI=' + android_abi,
                '-DANDROID_NATIVE_API_LEVEL=21',
                '-DANDROID_TOOLCHAIN_NAME=' + android_toolchain_name,
                '-DANDROID_STL=c++_shared'])
            self.project_file = 'build.ninja'
        if ios:
            cmake_call.extend(['-DIOS=1'])
        cmake_result = subprocess.call(cmake_call, cwd=self.build_directory)
        if cmake_result != 0:
            sys.exit(cmake_result)

    def buildTarget(self, target, sdk='macosx', arch='x86_64'):
        result = 0
        if self.use_ninja:
            result = subprocess.call([
                self.ninja_binary,
                '-C',
                self.build_directory,
                '-f',
                self.project_file,
                target])
        else:
            result = subprocess.call([
                'xcodebuild',
                '-project',
                self.project_file,
                '-target',
                target,
                '-sdk',
                sdk,
                '-arch',
                arch,
                '-configuration',
                self.build_type,
                'build'])
        if result != 0:
            sys.exit(result)

    def staticallyAnalyse(self, target, include_regex=None):
        diagnostics_key = 'diagnostics'
        files_key = 'files'
        exceptions_key = 'static_analyzer_exceptions'
        static_file_exceptions = []
        static_analyzer_result = subprocess.check_output([
            'xcodebuild',
            '-project',
            self.project_file,
            '-target',
            target,
            '-sdk',
            'macosx',
            '-configuration',
            self.build_type,
            '-dry-run',
            'analyze'])
        analyze_command = '--analyze'
        for line in static_analyzer_result.splitlines():
            if analyze_command not in line:
                continue
            static_analyzer_line_words = line.split()
            analyze_command_index = static_analyzer_line_words.index(
                analyze_command)
            source_file = static_analyzer_line_words[analyze_command_index + 1]
            if source_file.startswith(self.current_working_directory):
                source_file = source_file[
                    len(self.current_working_directory)+1:]
            if include_regex is not None:
                if not re.match(include_regex, source_file):
                    continue
            if source_file in self.statically_analyzed_files:
                continue
            self.build_print('Analysing ' + source_file)
            stripped_command = line.strip()
            clang_result = subprocess.call(stripped_command, shell=True)
            if clang_result:
                sys.exit(clang_result)
            self.statically_analyzed_files.append(source_file)
        static_analyzer_check_passed = True
        for root, dirnames, filenames in os.walk(self.build_directory):
            for filename in fnmatch.filter(filenames, '*.plist'):
                full_filepath = os.path.join(root, filename)
                static_analyzer_result = plistlib.readPlist(full_filepath)
                if 'clang_version' not in static_analyzer_result \
                        or files_key not in static_analyzer_result \
                        or diagnostics_key not in static_analyzer_result:
                    continue
                if len(static_analyzer_result[files_key]) == 0:
                    continue
                for static_analyzer_file in static_analyzer_result[files_key]:
                    if static_analyzer_file in static_file_exceptions:
                        continue
                    if self.current_working_directory not in static_analyzer_file:
                        continue
                    normalised_file = static_analyzer_file[
                        len(self.current_working_directory)+1:]
                    if normalised_file in \
                            self.build_configuration[exceptions_key]:
                        continue
                    self.build_print('Issues found in: ' + normalised_file)
                    for static_analyzer_issue in \
                            static_analyzer_result[diagnostics_key]:
                        self.pretty_printer.pprint(static_analyzer_issue)
                        sys.stdout.flush()
                    static_analyzer_check_passed = False
        if not static_analyzer_check_passed:
            sys.exit(1)
