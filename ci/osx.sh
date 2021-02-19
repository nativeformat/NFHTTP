#!/bin/bash
# Copyright (c) 2018 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# Exit on any non-zero status
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# Homebrew on circleci consistently fails with an error like:
#
# ==> Checking for dependents of upgraded formulae... Error: No such file or
# directory - /usr/local/Cellar/git/2.26.2_1
#
# Completely unpredictable, because it's just homebrew cleaning itself up and
# has nothing to do with the install itself! Just continue and hope the build
# fails if one of these tools is not installed.
if ! HOMEBREW_NO_AUTO_UPDATE=1 brew install \
    clang-format \
    cmake \
    ninja \
    wget ; then
    echo "Homebrew install had an error, review output and try manually."
fi

# Undo homebrew's potential meddling: https://github.com/pypa/pip/issues/5048
# Homebrew will upgrade python to 3.8, but virtualenv hard codes the path to 3.7
# in its shebang.
pip3 uninstall --yes virtualenv && pip3 install virtualenv

# Install virtualenv
virtualenv --python=$(which python2) nfhttp_env
source nfhttp_env/bin/activate

# Install Python Packages
pip install -r ${DIR}/requirements.txt

# Execute our python build tools
if [ -n "$BUILD_IOS" ]; then
    python ci/ios.py "$@"
else
    if [ -n "$BUILD_ANDROID" ]; then
    	brew cask install android-ndk

        python ci/android.py "$@"
    else
        python ci/osx.py "$@"
    fi
fi
