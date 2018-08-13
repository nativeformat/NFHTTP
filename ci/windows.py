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


def main():
    library_target = 'NFHTTP'
    cli_target = 'NFHTTPCLI'
    nfbuild = NFBuildWindows()
    nfbuild.build_print("Installing Dependencies")
    nfbuild.installDependencies()
    # Make our main build artifacts
    nfbuild.build_print("C++ Build Start (x86)")
    nfbuild.makeBuildDirectory()
    nfbuild.generateProject()
    targets = [library_target, cli_target]
    for target in targets:
        nfbuild.buildTarget(target)
    # nfbuild.runIntegrationTests()


if __name__ == "__main__":
    main()
