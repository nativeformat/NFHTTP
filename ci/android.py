#!/usr/bin/env python

import sys

from nfbuildosx import NFBuildOSX
from nfbuildwindows import NFBuildWindows
from nfbuildlinux import NFBuildLinux

from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("installDependencies", "Install dependencies")

    buildOptions.addOption("makeBuildDirectoryX86",
                           "Wipe existing build directory for X86 build.")
    buildOptions.addOption("generateProjectX86", "Regenerate project for X86 build")

    buildOptions.addOption("buildTargetLibraryX86", "Build Target: Library (X86)")

    buildOptions.addOption("makeBuildDirectoryArm64",
                           "Wipe existing build directory for ARM64 build.")
    buildOptions.addOption("generateProjectArm64", "Regenerate project for ARM64 build")

    buildOptions.addOption("buildTargetLibraryArm64", "Build Target: Library (ARM64)")

    buildOptions.addOption("buildLinux", "Build for Android Linux")
    buildOptions.addOption("buildWindows", "Build for Android Windows")

    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("build", "Production Build (Android OSX)", [
        'installDependencies',
        'makeBuildDirectoryX86',
        'generateProjectX86',
        'buildTargetLibraryX86',
        'makeBuildDirectoryArm64',
        'generateProjectArm64',
        'buildTargetLibraryArm64'
    ])

    buildOptions.addWorkflow("buildLinux", "Production Build (Android Linux)", [
        'installDependencies',
        'makeBuildDirectoryX86',
        'generateProjectX86',
        'buildTargetLibraryX86',
        'makeBuildDirectoryArm64',
        'generateProjectArm64',
        'buildTargetLibraryArm64'
    ])

    buildOptions.addWorkflow("buildWindows", "Production Build (Android Windows)", [
        'installDependencies',
        'makeBuildDirectoryX86',
        'generateProjectX86',
        'buildTargetLibraryX86',
        'makeBuildDirectoryArm64',
        'generateProjectArm64',
        'buildTargetLibraryArm64'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'

    if buildOptions.checkOption(options, 'buildLinux'):
        nfbuild = NFBuildLinux()
    elif buildOptions.checkOption(options, 'buildWindows'):
        nfbuild = NFBuildWindows()
    else:
        nfbuild = NFBuildOSX()

    if buildOptions.checkOption(options, 'installDependencies'):
        nfbuild.installDependencies(android=True)

    if buildOptions.checkOption(options, 'makeBuildDirectoryX86'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProjectX86'):
        nfbuild.generateProject(android=True, android_arm=False)

    if buildOptions.checkOption(options, 'buildTargetLibraryX86'):
        nfbuild.buildTarget(library_target)

    if buildOptions.checkOption(options, 'makeBuildDirectoryArm64'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProjectArm64'):
        nfbuild.generateProject(android=False, android_arm=True)

    if buildOptions.checkOption(options, 'buildTargetLibraryArm64'):
        nfbuild.buildTarget(library_target)


if __name__ == "__main__":
    main()
