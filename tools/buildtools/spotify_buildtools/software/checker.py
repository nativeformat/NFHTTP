import spotify_buildtools.utils as utils
import spotify_buildtools.schroot as schroot
import spotify_buildtools.software.softwarebase as sb
import os
from glob import glob
from distutils.spawn import find_executable
    
def setup(options):
    checker_output = sb.SoftwareBase('checker').install(options)
    
    checker_glob = "%s/checker*" % checker_output
    checker_extracted_matches = glob(checker_glob)
    if not len(checker_extracted_matches):
        raise Exception("Couldn't find extracted 'checker' root")
    checker_extracted_root = checker_extracted_matches[0]
    
    scan_build_script = "%s/bin/scan-build" % checker_extracted_root
    if not (os.path.isfile(scan_build_script)):
        raise Exception("Couldn't find scan-build script in %s" % scan_build_script)

    ccc_analyzer = "%s/libexec/ccc-analyzer" % checker_extracted_root
    cpp_analyzer = "%s/libexec/c++-analyzer" % checker_extracted_root 

    if not (os.path.isfile(ccc_analyzer)):
        raise Exception("Couldn't find ccc-analyzer in %s" % ccc_analyzer)
    if not (os.path.isfile(cpp_analyzer)):
        raise Exception("Couldn't find c++-analyzer in %s" % cpp_analyzer)
         
    utils.prepend_path("%s/bin" % checker_extracted_root)
    utils.prepend_path("%s/libexec" % checker_extracted_root)
