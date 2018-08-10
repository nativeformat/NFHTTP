import os

import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb

def setup(options):
    ninja_output = sb.SoftwareBase('ninja').install(options)
    utils.prepend_path(ninja_output)

    if not (os.path.isfile("%s/ninja" % ninja_output) or
            os.path.isfile("%s/ninja.exe" % ninja_output)):
        raise Exception("Couldn't find ninja binary in %s" % ninja_output)
