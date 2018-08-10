#!/bin/bash

# Must be run inside a schroot environment

# Exit on any non-zero status
set -e

# Install system dependencies
sudo apt-get install -y --no-install-recommends apt-utils
sudo apt-get install -y clang-3.9
sudo apt-get install -y clang-format-3.9
sudo apt-get install -y libcurl4-openssl-dev
sudo apt-get install -y libc++-dev
sudo apt-get install -y ninja-build

export CC=clang-3.9
export CXX=clang++-3.9

# Install virtualenv
VIRTUALENV_LOCAL_PATH='/virtualenv-15.1.0/virtualenv.py'
VIRTUALENV_PATH=`python tools/vulcan/bin/vulcan.py -v -f tools/virtualenv.vulcan -p virtualenv-15.1.0`
VIRTUALENV_PATH=$VIRTUALENV_PATH$VIRTUALENV_LOCAL_PATH
$VIRTUALENV_PATH nfhttp_env
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
