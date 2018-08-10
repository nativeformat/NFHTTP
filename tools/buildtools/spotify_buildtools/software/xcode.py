import glob
import os
import subprocess

import spotify_buildtools.software.softwarebase as sb
import spotify_buildtools.utils as utils

def accept_xcode_license(xcode_path):
    plistbuddy = '/usr/libexec/PlistBuddy'
    xcode_license_info_plist = os.path.join(xcode_path,
                                            'Contents',
                                            'Resources', 'LicenseInfo.plist')
    license_value = subprocess.check_output([plistbuddy,
                                             '-c', 'Print licenseID',
                                             xcode_license_info_plist]).strip()
    license_plist = '/Library/Preferences/com.apple.dt.Xcode.plist'
    license_key = 'IDELastGMLicenseAgreedTo'

    current_license_value = None
    try:
        c = 'Print %s' % license_key
        current_license_value = subprocess.check_output([plistbuddy,
                                                        '-c', c,
                                                        license_plist]).strip()
    except subprocess.CalledProcessError as e:
        pass

    xcode_version = subprocess.check_output([plistbuddy,
                                            '-c',
                                            'Print CFBundleShortVersionString',
                                            os.path.join(xcode_path,
                                                         'Contents',
                                                         'Info.plist')]
                                            ).strip()

    if current_license_value != license_value:
        #print ('Auto-accepting Xcode license (old=%s, new=%s)') % (current_license_value, license_value)
        if int(xcode_version.split('.')[0]) >= 5:
            # Run xcodebuild -license from Xcode 5 (requires sudo rights)
            # Accept the license
            subprocess.check_call(['sudo', '-E',
                                 os.path.join(xcode_path,
                                               'Contents', 'Developer', 'usr',
                                               'bin', 'xcodebuild'),
                                  '-license',
                                  'accept'])

        else:
            # We can use the legacy method with Xcode 4
            subprocess.check_call(['defaults',
                                   'write',
                                   'com.apple.dt.Xcode',
                                   license_key,
                                   license_value])

def setup(options):
    xcode_path = os.getenv('BUILDTOOLS_XCODE_OVERRIDE')
    if not xcode_path:
        xcode_output = sb.SoftwareBase('xcode').install(options)
        apps = glob.glob(os.path.join(xcode_output, "*.app"))

        if len(apps) != 1:
            raise Exception("Found %d app bundle in folder %s, expected only 1" % (len(apps), xcode_output))

        xcode_path = apps[0]

    if not os.path.isdir('%s/Contents/Developer/usr/bin' % xcode_path):
        raise Exception("Can't find %s/Contents/Developer/usr/bin" % xcode_path)

    os.environ['DEVELOPER_DIR'] = os.path.join(xcode_path, 'Contents/Developer')

    accept_xcode_license(xcode_path)
    utils.prepend_path('%s/Contents/Developer/usr/bin' % xcode_path)
    utils.prepend_path('%s/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin' % xcode_path)

    if not 'no_compiler_in_env' in options or not options.no_compiler_in_env:
        os.environ['CC'] = 'clang'
        os.environ['CXX'] = 'clang++'
