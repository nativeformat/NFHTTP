#!/bin/bash

# Exit on any non-zero status
set -e

# Install system dependencies
sudo apt-get update
sudo apt-get install -y --no-install-recommends apt-utils \
                                                clang-3.9 \
                                                clang-format-3.9 \
                                                libcurl4-openssl-dev \
                                                libc++-dev \
                                                ninja-build \
                                                python-virtualenv \
                                                wget \
                                                libyaml-dev

# Install cmake 3.6.x
wget --no-check-certificate https://cmake.org/files/v3.6/cmake-3.6.3-Linux-x86_64.sh
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
	python ci/androidlinux.py "$@"
else
	python ci/linux.py "$@"
fi
