#!/usr/bin/python
import os
import subprocess


def accept_xcode_license(xcode_parentdir):
    plistbuddy = '/usr/libexec/PlistBuddy'
    xcode_license_info_plist = os.path.join(xcode_parentdir,
                                            'Xcode.app/Contents/'
                                            'Resources/LicenseInfo.plist')
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
                                            os.path.join(xcode_parentdir,
                                                         'Xcode.app',
                                                         'Contents',
                                                         'Info.plist')]
                                            ).strip()

    if current_license_value != license_value:
        print ('Auto-accepting Xcode license '
               '(old=%s, new=%s)') % (current_license_value, license_value)
        if int(xcode_version.split('.')[0]) >= 5:
            # Run xcodebuild -license from Xcode 5 (requires sudo rights)
            env = os.environ.copy()
            env['DEVELOPER_DIR'] = os.path.join(xcode_parentdir, 'Xcode.app')
            # Accept the license
            subprocess.check_call(['sudo', '-E',
                                  os.path.join(xcode_parentdir, 'Xcode.app',
                                               'Contents', 'Developer', 'usr',
                                               'bin', 'xcodebuild'),
                                  '-license',
                                  'accept'], env=env)

        else:
            # We can use the legacy method with Xcode 4
            subprocess.check_call(['defaults',
                                   'write',
                                   'com.apple.dt.Xcode',
                                   license_key,
                                   license_value])
