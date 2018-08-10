import os
import spotify_buildtools.software.softwarebase as sb
import spotify_buildtools.schroot as schroot
import spotify_buildtools.utils as utils
from distutils.spawn import find_executable

def setup(options):
    cmake_output = sb.SoftwareBase('cmake').install(options)
    if not (os.path.isfile('%s/cmakebundle/bin/cmake' % cmake_output)
      or os.path.isfile('%s/cmakebundle/bin/cmake.exe' % cmake_output)):
        raise Exception("Can't find cmake binary in %s", cmake_output)

    utils.prepend_path('%s/cmakebundle/bin' % cmake_output)
