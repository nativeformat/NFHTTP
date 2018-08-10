#!/bin/bash

# Exit on any non-zero status
set -e

# Install virtualenv
VIRTUALENV_LOCAL_PATH='/virtualenv-15.1.0/virtualenv.py'
VIRTUALENV_PATH=`python tools/vulcan/bin/vulcan.py -v -f tools/virtualenv.vulcan -p virtualenv-15.1.0`
VIRTUALENV_PATH=$VIRTUALENV_PATH$VIRTUALENV_LOCAL_PATH
$VIRTUALENV_PATH nfhttp_env
source nfhttp_env/bin/activate

# Install Python Packages
pip install pyyaml
pip install flake8
pip install cmakelint
pip install requests

# Execute our python build tools
if [ -n "$BUILD_IOS" ]; then
    python ci/ios.py "$@"
else
    if [ -n "$BUILD_ANDROID" ]; then
        python ci/android.py "$@"
    else
        python ci/osx.py "$@"
    fi
fi
