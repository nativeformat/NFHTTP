import os
import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb

def setup(options):
    # Visual Studio 2015 / Windows 10 SDK
    vs_root = sb.SoftwareBase('visualstudio').install(options)
    vc_root = os.path.join(vs_root, 'VC')

    vc_tools_root = os.path.join(vc_root, 'Tools', 'MSVC')
    vc_tools_version = '14.10.25017'

    vc_redist_root = os.path.join(vc_root, 'Redist', 'MSVC')
    vc_redist_version = '14.10.25008'
    vc_redist_crt = 'Microsoft.VC150.CRT'

    sdk_root = os.path.join(vs_root, 'win10sdk')
    sdk_version = '10.0.15063.0'

    os.environ['VS_ROOT'] = vs_root
    os.environ['SDK_ROOT'] = sdk_root

    os.environ['INCLUDE'] = os.pathsep.join([
        os.path.join(sdk_root, 'Include', sdk_version, 'um'),
        os.path.join(sdk_root, 'Include', sdk_version, 'ucrt'),
        os.path.join(sdk_root, 'Include', sdk_version, 'shared'),
        os.path.join(sdk_root, 'Include', sdk_version, 'winrt'),
        os.path.join(vc_tools_root, vc_tools_version, 'include'),
        os.path.join(vc_tools_root, vc_tools_version, 'atlmfc', 'include'),
        os.environ.get('INCLUDE', '')])

    # 32-bit target architecture
    if options.arch == 'x86':
        os.environ['PATH'] = os.pathsep.join([
            os.path.join(sdk_root, 'bin', sdk_version, 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'bin', 'HostX64', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'bin', 'HostX64', 'x64'),
            os.path.join(vc_redist_root, vc_redist_version, 'x64', vc_redist_crt),
            os.path.join(vs_root, 'SystemCRT'),
            os.environ.get('PATH', '')])

        os.environ['LIB'] = os.pathsep.join([
            os.path.join(sdk_root, 'Lib', sdk_version, 'um', 'x86'),
            os.path.join(sdk_root, 'Lib', sdk_version, 'ucrt', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'lib', 'x86'),
            os.path.join(vc_tools_root, vc_tools_version, 'atlmfc', 'lib', 'x86'),
            os.environ.get('LIB', '')])

    # 64-bit target architecture
    elif options.arch == 'x86_64':
        os.environ['PATH'] = os.pathsep.join([
            os.path.join(sdk_root, 'bin', sdk_version, 'x64'),
            os.path.join(vc_tools_root, vc_tools_version, 'bin', 'HostX64', 'x64'),
            os.path.join(vc_redist_root, vc_redist_version, 'x64', vc_redist_crt),
            os.path.join(vs_root, 'SystemCRT'),
            os.environ.get('PATH', '')])

        os.environ['LIB'] = os.pathsep.join([
            os.path.join(sdk_root, 'Lib', sdk_version, 'um', 'x64'),
            os.path.join(sdk_root, 'Lib', sdk_version, 'ucrt', 'x64'),
            os.path.join(vc_tools_root, vc_tools_version, 'lib', 'x64'),
            os.path.join(vc_tools_root, vc_tools_version, 'atlmfc', 'lib', 'x64'),
            os.environ.get('LIB', '')])

    # Unsupported target architecture
    else:
        raise ValueError("Unsupported architecture '%s'!" % options.arch)
