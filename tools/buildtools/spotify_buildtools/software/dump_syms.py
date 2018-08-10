import os
import subprocess

import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb

def setup(options):
    dump_syms_output = sb.SoftwareBase('dump_syms').install(options)
    utils.prepend_path(dump_syms_output)

    if not (os.path.isfile(os.path.join(dump_syms_output, 'dump_syms')) or
            os.path.isfile(os.path.join(dump_syms_output, 'dump_syms.exe'))):
        raise Exception("Couldn't find 'dump_syms' binary in '%s'" % dump_syms_output)

    if options.platform == "windows":
        msdia_dll = os.path.join(dump_syms_output, 'msdia140.dll')
        subprocess.call(['regsvr32', '/s', msdia_dll])
