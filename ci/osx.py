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

import sys
import os

from nfbuildosx import NFBuildOSX
from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("debug", "Enable Debug Mode")
    buildOptions.addOption("installDependencies", "Install dependencies")
    buildOptions.addOption("lintCpp", "Lint CPP Files")
    buildOptions.addOption("lintCppWithInlineChange",
                           "Lint CPP Files and fix them")

    buildOptions.addOption("integrationTests", "Run Integration Tests")

    buildOptions.addOption("makeBuildDirectory",
                           "Wipe existing build directory")
    buildOptions.addOption("generateProject", "Regenerate xcode project")

    buildOptions.addOption("addressSanitizer",
                           "Enable Address Sanitizer in generate project")
    buildOptions.addOption("codeCoverage",
                           "Enable code coverage in generate project")
    buildOptions.addOption("curl", "Use curl in generate project")
    buildOptions.addOption("cpprest", "Use cpprest in generate project")

    buildOptions.addOption("buildTargetCLI", "Build Target: CLI")
    buildOptions.addOption("buildTargetLibrary", "Build Target: Library")
    buildOptions.addOption("gnuToolchain", "Build with gcc and libstdc++")
    buildOptions.addOption("llvmToolchain", "Build with clang and libc++")

    buildOptions.addOption("staticAnalysis", "Run Static Analysis")

    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("local_it", "Run local integration tests", [
        'debug',
        'integrationTests'
    ])

    buildOptions.addWorkflow("lint", "Run lint workflow", [
        'lintCppWithInlineChange'
    ])

    buildOptions.addWorkflow("address_sanitizer", "Run address sanitizer", [
        'debug',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'addressSanitizer',
        'buildTargetCLI',
        'integrationTests'
    ])

    buildOptions.addWorkflow("code_coverage", "Collect code coverage", [
        'debug',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'codeCoverage',
        'buildTargetCLI',
        'integrationTests'
    ])

    buildOptions.addWorkflow("build", "Production Build", [
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'buildTargetCLI',
        'buildTargetLibrary',
        'staticAnalysis',
        'integrationTests'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'
    cli_target = 'NFHTTPCLI'
    nfbuild = NFBuildOSX()

    if buildOptions.checkOption(options, 'debug'):
        nfbuild.build_type = 'Debug'

    if buildOptions.checkOption(options, 'lintCppWithInlineChange'):
        nfbuild.lintCPP(make_inline_changes=True)
    elif buildOptions.checkOption(options, 'lintCpp'):
        nfbuild.lintCPP(make_inline_changes=False)

    if buildOptions.checkOption(options, 'makeBuildDirectory'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProject'):
        nfbuild.generateProject(
            code_coverage='codeCoverage' in options,
            address_sanitizer='addressSanitizer' in options,
            use_curl='curl' in options,
            use_cpprest='cpprest' in options
        )

    if buildOptions.checkOption(options, 'generateProject'):
        if buildOptions.checkOption(options, 'gnuToolchain'):
            os.environ['CC'] = 'gcc-4.9'
            os.environ['CXX'] = 'g++-4.9'
            nfbuild.generateProject(gcc=True)
        elif buildOptions.checkOption(options, 'llvmToolchain'):
            os.environ['CC'] = 'clang-3.9'
            os.environ['CXX'] = 'clang++-3.9'
            nfbuild.generateProject(gcc=False)
        else:
            nfbuild.generateProject()

    if buildOptions.checkOption(options, 'buildTargetLibrary'):
        nfbuild.buildTarget(library_target)
        if buildOptions.checkOption(options, 'staticAnalysis'):
            nfbuild.staticallyAnalyse(library_target,
                                      include_regex='source/.*')

    if buildOptions.checkOption(options, 'buildTargetCLI'):
        nfbuild.buildTarget(cli_target)
        if buildOptions.checkOption(options, 'staticAnalysis'):
            nfbuild.staticallyAnalyse(cli_target,
                                      include_regex='source/.*')

    if buildOptions.checkOption(options, 'integrationTests'):
        nfbuild.runIntegrationTests()

    if buildOptions.checkOption(options, 'codeCoverage'):
        nfbuild.collectCodeCoverage()


if __name__ == "__main__":
    main()
