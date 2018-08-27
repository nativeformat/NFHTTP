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


class NFBuildLinux(NFBuild):
    clang_format_binary = 'clang-format-3.9'

    def __init__(self):
        super(self.__class__, self).__init__()
        self.cmake_binary = 'cmake'
        self.curl_directory = self.current_working_directory + '/libraries/curl'
        self.android_ndk_folder = '~/ndk'

    def generateProject(self,
                        code_coverage=False,
                        address_sanitizer=False,
                        thread_sanitizer=False,
                        undefined_behaviour_sanitizer=False,
                        ios=False,
                        android=False,
                        android_arm=False,
                        gcc=False):
        cmake_call = [self.cmake_binary, '..', '-GNinja']
        if self.build_type == 'Release':
            cmake_call.append('-DCREATE_RELEASE_BUILD=1')
        else:
            cmake_call.append('-DCREATE_RELEASE_BUILD=0')
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
        if gcc:
            cmake_call.extend(['-DLLVM_STDLIB=0'])
        else:
            cmake_call.extend(['-DLLVM_STDLIB=1'])
        cmake_result = subprocess.call(cmake_call, cwd=self.build_directory)
        if cmake_result != 0:
            sys.exit(cmake_result)

    def buildTarget(self, target, sdk='linux', arch='x86_64'):
        ninja_call = ['ninja', '-C', self.build_directory]
        result = subprocess.call(ninja_call, cwd=self.current_working_directory)
        if result != 0:
            sys.exit(result)

    def packageArtifacts(self):
        lib_name = 'libNFHTTP.a'
        cli_name = 'NFHTTPCLI'
        output_folder = os.path.join(self.build_directory, 'output')
        artifacts_folder = os.path.join(output_folder, 'NFHTTP')
        shutil.copytree('include', os.path.join(artifacts_folder, 'include'))
        source_folder = os.path.join(self.build_directory, 'source')
        lib_matches = self.find_file(source_folder, lib_name)
        cli_matches = self.find_file(source_folder, cli_name)
        shutil.copyfile(lib_matches[0], os.path.join(artifacts_folder, lib_name))
        shutil.copyfile(cli_matches[0], os.path.join(artifacts_folder, cli_name))
        output_zip = os.path.join(output_folder, 'libNFHTTP.zip')
        self.make_archive(artifacts_folder, output_zip)
