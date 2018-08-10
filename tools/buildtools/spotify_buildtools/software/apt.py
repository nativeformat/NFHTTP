import os
import spotify_buildtools.schroot as schroot
from distutils.spawn import find_executable

def setup(options):
    if options.platform != 'linux':
        raise Exception("Can't use apt on non-Linux platforms")
    if "apt_packages" in options and options.apt_packages:
        if schroot.has_client():
            schroot.client.install_apt(options.apt_packages)
        else:
            print "Make sure the following packages are installed: %s" % " ".join(options.apt_packages)
