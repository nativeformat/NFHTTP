#!/usr/bin/env python

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
        self.project_file = 'build.ninja'

    def installClangFormat(self):
        clang_format_vulcan_file = os.path.join('tools', 'clang-format.vulcan')
        clang_format_extraction_folder = self.vulcanDownload(
            clang_format_vulcan_file,
            'clang-format-5.0.0')
        self.clang_format_binary = os.path.join(
            os.path.join(
                os.path.join(
                    clang_format_extraction_folder,
                    'clang-format'),
                'bin'),
            'clang-format')

    def installNinja(self):
        ninja_vulcan_file = os.path.join(
            os.path.join(
                os.path.join(
                    os.path.join('tools', 'buildtools'),
                    'spotify_buildtools'),
                'software'),
            'ninja.vulcan')
        ninja_extraction_folder = self.vulcanDownload(
            ninja_vulcan_file,
            'ninja-1.6.0')
        self.ninja_binary = os.path.join(
            ninja_extraction_folder,
            'ninja')
        if 'PATH' not in os.environ:
            os.environ['PATH'] = ''
        if len(os.environ['PATH']) > 0:
            os.environ['PATH'] += os.pathsep
        os.environ['PATH'] += ninja_extraction_folder

    def installMake(self):
        make_vulcan_file = os.path.join('tools', 'make.vulcan')
        make_extraction_folder = self.vulcanDownload(
            make_vulcan_file,
            'make-4.2.1')
        make_bin_folder = os.path.join(
            make_extraction_folder,
            'bin')
        os.environ['PATH'] += os.pathsep + make_bin_folder

    def installVisualStudio(self):
        vs_vulcan_file = os.path.join(
            os.path.join(
                os.path.join(
                    os.path.join('tools', 'buildtools'),
                    'spotify_buildtools'),
                'software'),
            'visualstudio.vulcan')
        self.vs_extraction_folder = self.vulcanDownload(
            vs_vulcan_file,
            'visualstudio-2017')
        sdk_version = '10.0.15063.0'
        vc_tools_version = '14.10.25017'
        vc_redist_version = '14.10.25008'
        vc_redist_crt = 'Microsoft.VC150.CRT'
        vs_root = self.vs_extraction_folder
        sdk_root = os.path.join(vs_root, 'win10sdk')
        vc_root = os.path.join(vs_root, 'VC')
        vc_tools_root = os.path.join(vc_root, 'Tools', 'MSVC')
        vc_redist_root = os.path.join(vc_root, 'Redist', 'MSVC')
        os.environ['VS_ROOT'] = vs_root
        os.environ['SDK_ROOT'] = sdk_root
        os.environ['INCLUDE'] = os.pathsep.join([
            os.path.join(sdk_root, 'Include', sdk_version, 'um'),
            os.path.join(sdk_root, 'Include', sdk_version, 'ucrt'),
            os.path.join(sdk_root, 'Include', sdk_version, 'shared'),
            os.path.join(sdk_root, 'Include', sdk_version, 'winrt'),
            os.path.join(vc_tools_root, vc_tools_version, 'include'),
            os.path.join(vc_tools_root, vc_tools_version, 'atlmfc', 'include'),
            os.environ.get('INCLUDE', '')])
        os.environ['PATH'] = os.pathsep.join([
            os.path.join(sdk_root, 'bin', sdk_version, 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'bin', 'HostX64', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'bin', 'HostX64', 'x64'),
            os.path.join(vc_redist_root, vc_redist_version, 'x64', vc_redist_crt),
            os.path.join(vs_root, 'SystemCRT'),
            os.environ.get('PATH', '')])
        os.environ['LIB'] = os.pathsep.join([
            os.path.join(sdk_root, 'Lib', sdk_version, 'um', 'x86'),
            os.path.join(sdk_root, 'Lib', sdk_version, 'ucrt', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'lib', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'atlmfc', 'lib', 'x86'),
            os.environ.get('LIB', '')])
        os.environ['LIBPATH'] = os.pathsep.join([
            os.path.join(vc_tools_root, vc_tools_version, 'lib', 'x86', 'store', 'references'),
            os.path.join(sdk_root, 'UnionMetadata', sdk_version),
            os.environ.get('LIBPATH', '')])

    def installVulcanDependencies(self, android=False):
        super(self.__class__, self).installVulcanDependencies(android)
        self.installClangFormat()
        self.installMake()
        self.installVisualStudio()
        self.installNinja()

    def generateProject(self,
                        ios=False,
                        android=False,
                        android_arm=False):
        self.use_ninja = android or android_arm
        cmake_call = [
            self.cmake_binary,
            '..',
            '-GNinja']
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
                '-DANDROID_WINDOWS=1',
                '-DANDROID_STL=c++_shared'])
            self.project_file = 'build.ninja'
        else:
            cl_exe = os.path.join(self.vs_extraction_folder, 'VC', 'Tools', 'MSVC', '14.10.25017', 'bin', 'HostX64', 'x86', 'cl.exe').replace('\\', '/')
            rc_exe = os.path.join(self.vs_extraction_folder, 'win10sdk', 'bin', '10.0.15063.0', 'x64', 'rc.exe').replace('\\', '/')
            link_exe = os.path.join(self.vs_extraction_folder, 'VC', 'Tools', 'MSVC', '14.10.25017', 'bin', 'HostX64', 'x86', 'link.exe').replace('\\', '/')
            cmake_call.extend([
                '-DCMAKE_C_COMPILER=' + cl_exe,
                '-DCMAKE_CXX_COMPILER=' + cl_exe,
                '-DCMAKE_RC_COMPILER=' + rc_exe,
                '-DCMAKE_LINKER=' + link_exe,
                '-DWINDOWS=1'])
        cmake_result = subprocess.call(cmake_call, cwd=self.build_directory)
        if cmake_result != 0:
            sys.exit(cmake_result)

    def buildTarget(self, target, sdk='macosx', arch='x86_64'):
        result = subprocess.call([
            self.ninja_binary,
            '-C',
            self.build_directory,
            '-f',
            self.project_file,
            target])
        if result != 0:
            sys.exit(result)

    def targetBinary(self, target):
        bin_name = target + '.exe'
        for root, dirnames, filenames in os.walk(self.build_directory):
            for filename in fnmatch.filter(filenames, bin_name):
                full_target_file = os.path.join(root, filename)
                return full_target_file
        return ''

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

