import os
import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb
from distutils.spawn import find_executable

def setup(options):
    setattr(options, 'android_ndk-version', 'r16b')
    # Always respect the ANDROID_NDK environment variable to be able to use
    # own local NDK instead of NDK from artifactory. This is especially
    # important on Windows machines.
    if 'ANDROID_NDK' in os.environ and os.path.isdir(os.environ['ANDROID_NDK']):
        ndk_output = os.environ['ANDROID_NDK']
        print "Using NDK defined in ANDROID_NDK: %s" % ndk_output
    else:
        ndk_output = sb.SoftwareBase('android_ndk').install(options)

    if os.path.exists(os.path.join(ndk_output, "source.properties")):
        # r11 and higher have a source.properties file
        new_ndk = True
    else:
        # r10e and lower have a RELEASE.TXT file
        new_ndk = False

    if options.arch == 'armv7':
        android_abi = 'armeabi-v7a'
    elif options.arch == 'arm64':
        android_abi = 'arm64-v8a'
    elif options.arch == 'x86':
        android_abi = 'x86'
    elif options.arch == 'x86_64':
        android_abi = 'x86_64'
    else:
        raise ValueError("Unsupported value %s for android_arch option" % options.arch)

    os.environ["ANDROID_NDK"] = ndk_output
    os.environ["ANDROID_NDK_HOME"] = ndk_output

    options.extra_cmake.extend([
        '-DANDROID_NDK=%s' % ndk_output,
        '-DANDROID_ABI=%s' % android_abi
    ])
