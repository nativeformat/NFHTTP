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

# Install system dependencies
apt-get update
apt-get install sudo
sudo apt-get -q update
sudo apt-get install -y -q --no-install-recommends apt-utils \
    clang \
    clang-format \
    libcurl4-openssl-dev \
    libc++-dev \
    ninja-build \
    python-virtualenv \
    wget \
    libyaml-dev \
    libssl-dev \
    python-dev \
    python3-dev \
    git \
    unzip \
    software-properties-common \
    make \
    build-essentials \
    cmake

# Update submodules
git submodule sync
git submodule update --init --recursive

# Install virtualenv
virtualenv nfhttp_env
. nfhttp_env/bin/activate

# Install Python Packages
pip install -r ${PWD}/ci/requirements.txt

# Execute our python build tools
if [ -n "$BUILD_ANDROID" ]; then
    # Install Android NDK
    NDK='android-ndk-r17b-linux-x86_64'
    ZIP='zip'
    wget https://dl.google.com/android/repository/${NDK}.${ZIP} -O ${PWD}/${NDK}.${ZIP}
    unzip -o -q ${NDK}.${ZIP}
    rm -rf ~/ndk
    mv android-ndk-r17b ~/ndk

    chmod +x -R ~/ndk

    python ci/androidlinux.py "$@"
else
    python ci/linux.py "$@"
fi
