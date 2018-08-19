#!/usr/bin/env python

import sys

from nfbuildosx import NFBuildOSX
from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("lintCmake", "Lint cmake files")
    buildOptions.addOption("lintCpp", "Lint CPP Files")
    buildOptions.addOption("lintCppWithInlineChange",
                           "Lint CPP Files and fix them")
    buildOptions.addOption("makeBuildDirectory",
                           "Wipe existing build directory")
    buildOptions.addOption("generateProject", "Regenerate xcode project")
    buildOptions.addOption("buildTargetIphoneSimulator",
                           "Build Target: iPhone Simulator")
    buildOptions.addOption("buildTargetIphoneOS", "Build Target: iPhone OS")

    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("lint", "Run lint workflow", [
        'lintCmake',
        'lintCppWithInlineChange'
    ])

    buildOptions.addWorkflow("build", "Production Build", [
        'lintCmake',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'buildTargetIphoneSimulator',
        'buildTargetIphoneOS',
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'
    nfbuild = NFBuildOSX()

    if buildOptions.checkOption(options, 'lintCmake'):
        nfbuild.lintCmake()

    if buildOptions.checkOption(options, 'lintCppWithInlineChange'):
        nfbuild.lintCPP(make_inline_changes=True)
    elif buildOptions.checkOption(options, 'lintCpp'):
        nfbuild.lintCPP(make_inline_changes=False)

    if buildOptions.checkOption(options, 'makeBuildDirectory'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProject'):
        nfbuild.generateProject(ios=True)

    if buildOptions.checkOption(options, 'buildTargetIphoneSimulator'):
        nfbuild.buildTarget(library_target,
                            sdk='iphonesimulator',
                            arch='x86_64')

    if buildOptions.checkOption(options, 'buildTargetIphoneOS'):
        nfbuild.buildTarget(library_target, sdk='iphoneos', arch='arm64')


if __name__ == "__main__":
    main()
