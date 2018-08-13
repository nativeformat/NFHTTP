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
sudo apt-get update
sudo apt-get install -y --no-install-recommends apt-utils \
                                                libasound2-dev \
                                                clang-format-3.9 \
                                                ninja-build \
                                                clang-3.9 \
                                                libc++-dev \
                                                python-pip \
                                                python-virtualenv \
                                                wget \
                                                libyaml-dev \
                                                python-dev \
                                                python3-dev \
                                                git \
                                                unzip \
                                                software-properties-common \
                                                python-software-properties

# Extra repo for gcc-4.9 so we don't have to use 4.8
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-get install -y --no-install-recommends gcc-4.9 \
                                                g++-4.9

sudo apt-get install -y --reinstall binutils

# Install cmake 3.6.x
wget https://cmake.org/files/v3.6/cmake-3.6.3-Linux-x86_64.sh
chmod +x cmake-3.6.3-Linux-x86_64.sh
sudo sh cmake-3.6.3-Linux-x86_64.sh --prefix=/usr/local --exclude-subdir

# Install virtualenv
virtualenv nfhttp_env
. nfhttp_env/bin/activate

# Install Python Packages
pip install pyyaml \
			flake8 \
			cmakelint \
			requests

# Execute our python build tools
if [ -n "$BUILD_ANDROID" ]; then
    # Install Android NDK
    wget https://dl.google.com/android/repository/android-ndk-r17b-linux-x86_64.zip
    unzip -q android-ndk-r17b-linux-x86_64.zip
    mv android-ndk-r17b ~/ndk
    chmod +x -R ~/ndk
	python ci/androidlinux.py "$@"
else
	python ci/linux.py "$@"
fi
