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

from nfbuildwindows import NFBuildWindows
from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("installDependencies", "Install dependencies")
    buildOptions.addOption("makeBuildDirectory",
                           "Wipe existing build directory")
    buildOptions.addOption("generateProject", "Regenerate project")
    buildOptions.addOption("buildTargetCLI",
                           "Build Target: CLI")
    buildOptions.addOption("buildTargetLibrary", "Build Target: Library")
    buildOptions.addOption("packageArtifacts", "Package the binary artifacts")
    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("build", "Production Build", [
        'installDependencies',
        'makeBuildDirectory',
        'generateProject',
        'buildTargetCLI',
        'buildTargetLibrary',
        'packageArtifacts'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'
    cli_target = 'NFHTTPCLI'
    nfbuild = NFBuildWindows()

    if buildOptions.checkOption(options, 'installDependencies'):
        nfbuild.installDependencies()

    if buildOptions.checkOption(options, 'makeBuildDirectory'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProject'):
        nfbuild.generateProject(ios=True)

    if buildOptions.checkOption(options, 'buildTargetLibrary'):
        nfbuild.buildTarget(library_target)

    if buildOptions.checkOption(options, 'buildTargetCLI'):
        nfbuild.buildTarget(cli_target)

    if buildOptions.checkOption(options, "packageArtifacts"):
        nfbuild.packageArtifacts()


if __name__ == "__main__":
    main()
