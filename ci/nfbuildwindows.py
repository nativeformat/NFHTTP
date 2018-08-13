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
import time

from distutils import dir_util
from nfbuild import NFBuild


class NFBuildWindows(NFBuild):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.project_file = 'NFHTTP.sln'
        self.cmake_binary = 'cmake'
        self.android = False

    def generateProject(self,
                        ios=False,
                        android=False,
                        android_arm=False):
        self.use_ninja = android or android_arm
        cmake_call = [
            self.cmake_binary,
            '..',
            '-G']
        if android or android_arm:
            self.android = True
            self.build_project = 'build.ninja'
            android_abi = 'x86_64'
            android_toolchain_name = 'x86_64-llvm'
            if android_arm:
                android_abi = 'arm64-v8a'
                android_toolchain_name = 'arm64-llvm'
            cmake_call.extend([
                'Ninja',
                '-DANDROID=1',
                '-DCMAKE_TOOLCHAIN_FILE=' + self.android_ndk_folder + '/build/cmake/android.toolchain.cmake',
                '-DANDROID_NDK=' + self.android_ndk_folder,
                '-DANDROID_ABI=' + android_abi,
                '-DANDROID_NATIVE_API_LEVEL=21',
                '-DANDROID_TOOLCHAIN_NAME=' + android_toolchain_name,
                '-DANDROID_WINDOWS=1',
                '-DANDROID_STL=c++_shared'])
            self.project_file = 'build.ninja'
        else:
            cl_exe = 'cl.exe'
            rc_exe = 'rc.exe'
            link_exe = 'link.exe'
            cmake_call.extend([
                'Visual Studio 15 2017 Win64',
                '-DCMAKE_SYSTEM_NAME=WindowsStore',
                '-DCMAKE_SYSTEM_VERSION=10.0'])
        cmake_result = subprocess.call(cmake_call, cwd=self.build_directory)
        if cmake_result != 0:
            sys.exit(cmake_result)

    def buildTarget(self, target, sdk='macosx', arch='x86_64'):
        result = 0
        if self.android:
            result = subprocess.call([
                self.ninja_binary,
                '-C',
                self.build_directory,
                '-f',
                self.project_file,
                target])
        else:
            result = subprocess.call([
                'msbuild.exe',
                os.path.join(self.build_directory, 'NFHTTP.sln'),
                '/t:NFHTTP;' + target])
        if result != 0:
            sys.exit(result)

    def targetBinary(self, target):
        bin_name = target + '.exe'
        for root, dirnames, filenames in os.walk(self.build_directory):
            for filename in fnmatch.filter(filenames, bin_name):
                full_target_file = os.path.join(root, filename)
                return full_target_file
        return ''

    def packageArtifacts(self):
        lib_name = 'NFHTTP.lib'
        cli_name = 'NFHTTPCLI.exe'
        output_folder = os.path.join(self.build_directory, 'output')
        artifacts_folder = os.path.join(output_folder, 'NFHTTP')
        shutil.copytree('include', os.path.join(artifacts_folder, 'include'))
        source_folder = os.path.join(self.build_directory, 'source')
        lib_matches = self.find_file(source_folder, lib_name)
        cli_matches = self.find_file(source_folder, cli_name)
        shutil.copyfile(lib_matches[0], os.path.join(artifacts_folder, lib_name))
        if not self.android:
            shutil.copyfile(cli_matches[0], os.path.join(artifacts_folder, cli_name))
        output_zip = os.path.join(output_folder, 'libNFHTTP.zip')
        self.make_archive(artifacts_folder, output_zip)
        if self.android:
            final_zip_name = 'libNFHTTP-androidx86.zip'
            if self.android_arm:
                final_zip_name = 'libNFHTTP-androidArm64.zip'
            shutil.copyfile(output_zip, final_zip_name)

    def runIntegrationTests(self):
        # Build the CLI target
        cli_target_name = 'NFHTTPCLI'
        cli_binary = self.targetBinary(cli_target_name)
        self.buildTarget(cli_target_name)
        # Launch the dummy server
        root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        cwd = os.path.join(os.path.join(root_path, 'resources'), 'localhost')
        cmd = 'python -m SimpleHTTPServer 6582'
        pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd)
        print 'CLI binary: ' + str(cli_binary)
        print 'CWD: ' + str(cwd)
        time.sleep(3)
        cli_result = self.runIntegrationTestsUnderDummyServer(cli_binary, root_path)
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(pro.pid)])
        if cli_result:
            sys.exit(cli_result)

