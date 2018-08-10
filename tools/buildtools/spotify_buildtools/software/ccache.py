import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb
import spotify_buildtools.schroot as schroot
import atexit
import os
import platform
import re
import shutil
import subprocess
import tempfile
from distutils.spawn import find_executable

def dump_stats(ccache, options):
    if False and not options.build:
        return
    stats = subprocess.check_output([ccache, '-s'])
    if not 'TEAMCITY_PROJECT_NAME' in os.environ:
        print stats
    else:
        direct_hits = int(re.search('\(direct\)\s+(\d+)', stats).group(1))
        preprocessed_hits = int(re.search('\(preprocessed\)\s+(\d+)', stats).group(1))
        files_in_cache = int(re.search('files in cache\s+(\d+)', stats).group(1))
        cache_misses = int(re.search('cache miss\s+(\d+)', stats).group(1))
        total_hits = direct_hits + preprocessed_hits
        total = total_hits + cache_misses
        hit_percent = round(100.0 * total_hits / total, 4) if total else 100
        miss_percent = round(100 - hit_percent, 4)
        for params in (
            ('CCacheCacheHitDirect', direct_hits),
            ('CCacheCacheHitPreprocessed', preprocessed_hits),
            ('CCacheCacheHitMiss', cache_misses),
            ('CCacheFilesInCache', files_in_cache),
            ('CCacheSynthesizedCacheHit', total_hits),
            ('CCacheSynthesizedCacheHitPercent', hit_percent),
            ('CCacheSynthesizedCacheMissPercent', miss_percent)):
            print "##teamcity[buildStatisticValue key='%s' value='%s']" % params

def setup(options):
    host_platform = platform.system().lower()
    if host_platform == 'darwin':
        host_platform = 'osx'

    ccache_output = sb.SoftwareBase('ccache').install(options)
    utils.prepend_path(ccache_output)

    ccache_paths = [
        os.path.join(ccache_output, 'ccache'),
        os.path.join(ccache_output, 'clcache.exe'),
    ]
    try:
        ccache_bin = os.path.normpath(next(iter(filter(os.path.isfile, ccache_paths)), None))
    except:
        raise Exception('''Couldn't find ccache in any of %s %s''' % (os.getcwd(), ccache_paths))

    ccache_size = 20 * (1024 ** 3) # 20 GB by default
    if 'ccache_size' in options:
        ccache_size = int(options.ccache_size)

    if host_platform == 'windows':
        os.environ["CC"] = ccache_bin
        os.environ["CXX"] = ccache_bin

        # Check current cache size
        ccache_size_line = [l for l in subprocess.check_output([ccache_bin, '-s']).strip().splitlines() if 'maximum cache size' in l][0]
        current_ccache_size = [int(s) for s in ccache_size_line.split() if s.isdigit()][0]

        if current_ccache_size < ccache_size:
            # Increase the cache size if it's lower that the required size
            subprocess.check_call([ccache_bin, '-M', "%d" % ccache_size])
    else:
        if options.platform == 'android':
           os.environ["NDK_CCACHE"] = ccache_bin
        else:
            # Create symlinks to ccache with the name of the compiler we want it to use
            # and add that folder to the PATH
            if not 'build_dir' in options:
                # If it's not running from "cmake", there's no build_dir option and we create
                # the symlinks in a temp folder that is remove on exit
                options.build_dir = tempfile.mkdtemp()
                atexit.register(shutil.rmtree, options.build_dir)
            bindir = "%s/bin" % options.build_dir

            if not os.path.isdir(bindir):
                os.makedirs(bindir)
            utils.prepend_path(bindir)

            # Create symlinks with the same name as the compiler pointing to ccache
            # Then set CC and CXX pointing to those symlinks, ccache when run will
            # find the compiler with the same name as the symlink in the path
            cc_path = "%s/%s" % (bindir, (os.path.basename(os.environ['CC']) if 'CC' in os.environ else 'cc'))
            cxx_path = "%s/%s" % (bindir, (os.path.basename(os.environ['CXX']) if 'CXX' in os.environ else 'c++'))
            if os.path.exists(cc_path):
                if os.path.realpath(cc_path) != ccache_bin:
                    os.remove(cc_path)
            if not os.path.exists(cc_path):
                os.symlink("%s/ccache" % ccache_output, cc_path)
            if os.path.exists(cxx_path):
                if os.path.realpath(cxx_path) != ccache_bin:
                    os.remove(cxx_path)
            if not os.path.exists(cxx_path):
                os.symlink("%s/ccache" % ccache_output, cxx_path)
            os.environ["CC"] = cc_path
            os.environ["CXX"] = cxx_path

        # Workaround bug in ccache 3.1.9 and clang, remove after upgrading ccache
        os.environ["CCACHE_CPP2"] = "1"
        os.environ["CCACHE_COMPRESS"] = "1"
        os.environ["USE_CCACHE"] = "1"

        # Check current cache size, it's in the form of X.Y GB
        ccache_size_line = [l for l in subprocess.check_output([ccache_bin, '-s']).strip().splitlines() if 'max cache size' in l]

        if not ccache_size_line:
            current_ccache_size = 0
        else:
            current_ccache_size = float(ccache_size_line[0].split()[-2]) * (1000 ** 3) # Assume it's in GB

        if current_ccache_size < ccache_size:
            # Increase the cache size
            subprocess.check_call([ccache_bin, '-M', "%dG" % (ccache_size / (1000 ** 3))])

    # Reset stats
    subprocess.check_call([ccache_bin, '-z'])
    atexit.register(lambda: dump_stats(ccache_bin, options))

