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
                                                python-virtualenv

export CC=clang-3.9
export CXX=clang++-3.9

# Install virtualenv
virtualenv nfhttp_env
. nfhttp_env/bin/activate

# Install Python Packages
pip install pyyaml
pip install flake8
pip install cmakelint
pip install requests

# Execute our python build tools
if [ -n "$BUILD_ANDROID" ]; then
	python ci/androidlinux.py "$@"
else
	python ci/linux.py "$@"
fi
