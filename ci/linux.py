#!/usr/bin/env python

import sys

from nfbuildlinux import NFBuildLinux
from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("debug", "Enable Debug Mode")
    buildOptions.addOption("installDependencies", "Install dependencies")
    buildOptions.addOption("lintCmake", "Lint cmake files")
    buildOptions.addOption("lintCppWithInlineChange",
                           "Lint CPP Files and fix them")
    buildOptions.addOption("makeBuildDirectory",
                           "Wipe existing build directory")
    buildOptions.addOption("generateProject", "Regenerate project")
    buildOptions.addOption("buildTargetLibrary", "Build Target: Library")
    buildOptions.addOption("gnuToolchain", "Build with gcc and libstdc++")
    buildOptions.addOption("llvmToolchain", "Build with clang and libc++")

    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("lint", "Run lint workflow", [
        'lintCmake',
        'lintCppWithInlineChange'
    ])

    buildOptions.addWorkflow("clang_build", "Production Clang Build", [
        'llvmToolchain',
        'lintCmake',
        'makeBuildDirectory',
        'generateProject',
        'buildTargetLibrary'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'
    nfbuild = NFBuildLinux()

    if buildOptions.checkOption(options, 'debug'):
        nfbuild.build_type = 'Debug'

    if buildOptions.checkOption(options, 'lintCmake'):
        nfbuild.lintCmake()

    if buildOptions.checkOption(options, 'lintCppWithInlineChange'):
        nfbuild.lintCPP(make_inline_changes=True)

    if buildOptions.checkOption(options, 'makeBuildDirectory'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProject'):
        if buildOptions.checkOption(options, 'gnuToolchain'):
            os.environ['CC'] = 'gcc-4.9'
            os.environ['CXX'] = 'g++-4.9'
            nfbuild.generateProject(gcc=True)
        elif buildOptions.checkOption(options, 'llvmToolchain'):
            os.environ['CC'] = 'clang-3.9'
            os.environ['CXX'] = 'clang++-3.9'
            nfbuild.generateProject(gcc=False)
        else:
            nfbuild.generateProject()

    if buildOptions.checkOption(options, 'buildTargetLibrary'):
        nfbuild.buildTarget(library_target)


if __name__ == "__main__":
    main()
