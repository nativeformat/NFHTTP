#!/usr/bin/env python

import sys

from nfbuildosx import NFBuildOSX
from build_options import BuildOptions


def main():
    buildOptions = BuildOptions()
    buildOptions.addOption("debug", "Enable Debug Mode")
    buildOptions.addOption("installDependencies", "Install dependencies")

    buildOptions.addOption("lintCmake", "Lint cmake files")
    buildOptions.addOption("lintCpp", "Lint CPP Files")
    buildOptions.addOption("lintCppWithInlineChange",
                           "Lint CPP Files and fix them")

    buildOptions.addOption("integrationTests", "Run Integration Tests")

    buildOptions.addOption("makeBuildDirectory",
                           "Wipe existing build directory")
    buildOptions.addOption("generateProject", "Regenerate xcode project")

    buildOptions.addOption("addressSanitizer",
                           "Enable Address Sanitizer in generate project")
    buildOptions.addOption("codeCoverage",
                           "Enable code coverage in generate project")
    buildOptions.addOption("curl", "Use curl in generate project")
    buildOptions.addOption("cpprest", "Use cpprest in generate project")

    buildOptions.addOption("buildTargetCLI", "Build Target: CLI")
    buildOptions.addOption("buildTargetLibrary", "Build Target: Library")

    buildOptions.addOption("staticAnalysis", "Run Static Analysis")
    buildOptions.addOption("makeCLI", "Deploy CLI Binary")
    buildOptions.addOption("packageArtifacts", "Package the artifacts produced by the build")

    buildOptions.setDefaultWorkflow("Empty workflow", [])

    buildOptions.addWorkflow("local_it", "Run local integration tests", [
        'debug',
        'installDependencies',
        'lintCmake',
        'integrationTests'
    ])

    buildOptions.addWorkflow("lint", "Run lint workflow", [
        'installDependencies',
        'lintCmake',
        'lintCppWithInlineChange'
    ])

    buildOptions.addWorkflow("address_sanitizer", "Run address sanitizer", [
        'debug',
        'installDependencies',
        'lintCmake',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'addressSanitizer',
        'buildTargetCLI',
        'integrationTests'
    ])

    buildOptions.addWorkflow("code_coverage", "Collect code coverage", [
        'debug',
        'installDependencies',
        'lintCmake',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'codeCoverage',
        'buildTargetCLI',
        'integrationTests'
    ])

    buildOptions.addWorkflow("build", "Production Build", [
        'installDependencies',
        'lintCmake',
        'lintCpp',
        'makeBuildDirectory',
        'generateProject',
        'buildTargetCLI',
        'buildTargetLibrary',
        'staticAnalysis',
        'integrationTests'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    library_target = 'NFHTTP'
    cli_target = 'NFHTTPCLI'
    nfbuild = NFBuildOSX()

    if buildOptions.checkOption(options, 'debug'):
        nfbuild.build_type = 'Debug'

    if buildOptions.checkOption(options, 'installDependencies'):
        nfbuild.installDependencies()

    if buildOptions.checkOption(options, 'lintCmake'):
        nfbuild.lintCmake()

    if buildOptions.checkOption(options, 'lintCppWithInlineChange'):
        nfbuild.lintCPP(make_inline_changes=True)
    elif buildOptions.checkOption(options, 'lintCpp'):
        nfbuild.lintCPP(make_inline_changes=False)

    if buildOptions.checkOption(options, 'makeBuildDirectory'):
        nfbuild.makeBuildDirectory()

    if buildOptions.checkOption(options, 'generateProject'):
        nfbuild.generateProject(
            code_coverage='codeCoverage' in options,
            address_sanitizer='addressSanitizer' in options,
            use_curl='curl' in options,
            use_cpprest='cpprest' in options
            )

    if buildOptions.checkOption(options, 'buildTargetLibrary'):
        nfbuild.buildTarget(library_target)
        if buildOptions.checkOption(options, 'staticAnalysis'):
            nfbuild.staticallyAnalyse(library_target,
                                      include_regex='source/.*')

    if buildOptions.checkOption(options, 'buildTargetCLI'):
        nfbuild.buildTarget(cli_target)
        if buildOptions.checkOption(options, 'staticAnalysis'):
            nfbuild.staticallyAnalyse(cli_target,
                                      include_regex='source/.*')

    if buildOptions.checkOption(options, 'integrationTests'):
        nfbuild.runIntegrationTests()

    if buildOptions.checkOption(options, 'codeCoverage'):
        nfbuild.collectCodeCoverage()


if __name__ == "__main__":
    main()
