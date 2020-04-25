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

# Install system dependencies
# Don't use Brewfile because tapping bundle takes so long that the build times out
# https://ideas.circleci.com/ideas/CCI-I-1197
brew install clang-format
brew install cmake
brew install ninja
brew install wget

# Should fix the error: /usr/local/opt/python/bin/python2.7: bad interpreter: No such file or directory
# We really should move to python3
ln -s "/usr/local/bin/python" "/usr/local/opt/python/bin/python2.7"

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
