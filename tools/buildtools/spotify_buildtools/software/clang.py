from glob import glob
import os
import spotify_buildtools.software.softwarebase as sb
import spotify_buildtools.utils as utils
import spotify_buildtools.schroot as schroot

def setup(options):
    symbolizer_glob = None
    if options.platform == 'linux':
        if schroot.has_client():
            schroot.client.install_apt(['binutils'])

        clang_path = sb.SoftwareBase('clang').install(options)
        symbolizer_glob = '%s/bin/llvm-symbolizer' % clang_path
        utils.prepend_path('%s/bin' % clang_path)
        os.environ['CC'] = '%s/bin/clang' % clang_path
        os.environ['CXX'] = '%s/bin/clang++' % clang_path

        # Add gold to the PATH
        utils.prepend_path('/usr/lib/gold-ld')
    elif options.platform == 'osx':
        clang_path = sb.SoftwareBase('clang').install(options)
        symbolizer_glob = '%s/bin/llvm-symbolizer' % clang_path
        utils.prepend_path('%s/bin' % clang_path)
        os.environ['DYLD_LIBRARY_PATH'] = glob(
            '%s/lib/clang/**/lib/darwin/' % clang_path)[0]
        os.environ['CC'] = '%s/bin/clang' % clang_path
        os.environ['CXX'] = '%s/bin/clang++' % clang_path

    if symbolizer_glob:
        symbolizers = glob(symbolizer_glob)
        if not len(symbolizers):
            raise Exception('llvm-symbolizer not found')
        os.environ['ASAN_SYMBOLIZER_PATH'] = symbolizers[0]

    # Create a gcov symlink pointing to llvm-cov
    gcov_path = '%s/bin/gcov' % (options.build_dir)
    llvmcov_path = '%s/bin/llvm-cov' % clang_path
    if os.path.exists(gcov_path):
        if os.path.realpath(gcov_path) != llvmcov_path:
            os.remove(gcov_path)
    if not os.path.exists(gcov_path):
        if not os.path.exists('%s/bin' % options.build_dir):
            os.makedirs('%s/bin' % options.build_dir)
        os.symlink(llvmcov_path, gcov_path)
    utils.prepend_path('%s/bin' % options.build_dir)
