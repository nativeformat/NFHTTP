#!/bin/bash -ex

# This script downloads CMake binary distributions from http://www.cmake.org
# and strips unnecessary binaries and documentation to reduce the file size
# for upload to Artifactory.

if [ $# -ne 1 ] ; then
    echo >> /dev/stderr "ERROR: Syntax: package_cmake.sh <version>"
    exit 1
fi

CMAKE_VERSION=$1
CMAKE_BASE_VERSION="${CMAKE_VERSION%.*}"
CMAKE_BASE_URL="https://cmake.org/files/v${CMAKE_BASE_VERSION}"

CMAKE_LINUX_TAR_GZ="cmake-${CMAKE_VERSION}-Linux-x86_64.tar.gz"
CMAKE_DARWIN_TAR_GZ="cmake-${CMAKE_VERSION}-Darwin-x86_64.tar.gz"
CMAKE_WINDOWS_ZIP="cmake-${CMAKE_VERSION}-win64-x64.zip"

CMAKE_LINUX_TAR="${CMAKE_LINUX_TAR_GZ%.*}"
CMAKE_DARWIN_TAR="${CMAKE_DARWIN_TAR_GZ%.*}"

CMAKE_LINUX_DIR="${CMAKE_LINUX_TAR%.*}"
CMAKE_DARWIN_DIR="${CMAKE_DARWIN_TAR%.*}/CMake.app/Contents"
CMAKE_WINDOWS_DIR="${CMAKE_WINDOWS_ZIP%.*}"

CMAKE_BUNDLE_DIR="cmakebundle"
CMAKE_BUNDLE_LINUX_TAR_GZ="cmake-${CMAKE_VERSION}-linux.tar.gz"
CMAKE_BUNDLE_DARWIN_TAR_GZ="cmake-${CMAKE_VERSION}-osx.tar.gz"
CMAKE_BUNDLE_WINDOWS_TAR_GZ="cmake-${CMAKE_VERSION}-win32.tar.gz"

#
# Package Linux distribution.
#

if [ -d "$CMAKE_BUNDLE_DIR" ]; then
  rm -r $CMAKE_BUNDLE_DIR
fi

mkdir -p $CMAKE_BUNDLE_DIR

curl -s "${CMAKE_BASE_URL}/${CMAKE_LINUX_TAR_GZ}" | tar --checkpoint=.1000 -xz -P

mv "$CMAKE_LINUX_DIR/bin" $CMAKE_BUNDLE_DIR
mv "$CMAKE_LINUX_DIR/share" $CMAKE_BUNDLE_DIR
rm "$CMAKE_BUNDLE_DIR/bin/ccmake"
rm "$CMAKE_BUNDLE_DIR/bin/cmake-gui"

GZIP=-9 tar --checkpoint=.1000 -czf $CMAKE_BUNDLE_LINUX_TAR_GZ $CMAKE_BUNDLE_DIR

#
# Package macOS distribution.
#

if [ -d "$CMAKE_BUNDLE_DIR" ]; then
  rm -r $CMAKE_BUNDLE_DIR
fi

mkdir -p $CMAKE_BUNDLE_DIR

curl -s "${CMAKE_BASE_URL}/${CMAKE_DARWIN_TAR_GZ}" | tar --checkpoint=.1000 -xz -P

mv "$CMAKE_DARWIN_DIR/bin" $CMAKE_BUNDLE_DIR
mv "$CMAKE_DARWIN_DIR/share" $CMAKE_BUNDLE_DIR
rm "$CMAKE_BUNDLE_DIR/bin/ccmake"
rm "$CMAKE_BUNDLE_DIR/bin/cmake-gui"

GZIP=-9 tar --checkpoint=.1000 -czf $CMAKE_BUNDLE_DARWIN_TAR_GZ $CMAKE_BUNDLE_DIR

#
# Package Windows distribution.
#

if [ -d "$CMAKE_BUNDLE_DIR" ]; then
  rm -r $CMAKE_BUNDLE_DIR
fi

mkdir -p $CMAKE_BUNDLE_DIR

curl -sO "${CMAKE_BASE_URL}/${CMAKE_WINDOWS_ZIP}"
unzip -oq $CMAKE_WINDOWS_ZIP
rm $CMAKE_WINDOWS_ZIP

mv "$CMAKE_WINDOWS_DIR/bin" $CMAKE_BUNDLE_DIR
mv "$CMAKE_WINDOWS_DIR/share" $CMAKE_BUNDLE_DIR
rm "$CMAKE_BUNDLE_DIR/bin/cmake-gui.exe"

GZIP=-9 tar --checkpoint=.1000 -czf $CMAKE_BUNDLE_WINDOWS_TAR_GZ $CMAKE_BUNDLE_DIR

