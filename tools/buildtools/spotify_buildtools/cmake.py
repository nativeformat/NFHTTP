import argparse
import multiprocessing
import os
import shutil
import sys

from spotify_buildtools.utils import run_command, str2bool, ExtendAction, find_software, log_section

def escape_teamcity_message(unfiltered):
    return str(unfiltered).replace('|','||').replace("'", "|'").replace('\n','|n').replace('\r','|r').replace('[','|[').replace(']','|]')

#################
# Class used to abstract multiple generators with common operations
# while doing the right thing (tm)
#################
class CMake:
    def __init__(self,
                 project_dir = os.getcwd(),
                 build_dir = "build",
                 build_concurrency = None,
                 configuration = "Release",
                 generator = "Unix Makefiles",
                 toolchain = None,
                 test_parallelize = False,
                 test_filter = None,
                 extra_args = None):
        self._project_dir = project_dir
        self._build_dir = build_dir
        self._build_concurrency = build_concurrency
        self._configuration = configuration
        self._generator = generator
        self._toolchain = toolchain
        self._extra_args = extra_args
        self._test_parallelize = test_parallelize
        self._test_filter = test_filter

    def generate(self, args = None, cmake_args = None):
        try:
            if args is None: args = []
            if cmake_args is None: cmake_args = []

            if not os.path.isdir(self._build_dir):
                os.makedirs(self._build_dir)

            args.append("cmake")

            cmake_args.append(self._project_dir)
            cmake_args.append('-G "%s"' % self._generator)

            if not self._generator.startswith("Visual Studio") and not self._generator == 'Xcode':
                cmake_args.append("-DCMAKE_BUILD_TYPE=%s" % self._configuration)
            if self._toolchain:
                cmake_args.append("-DCMAKE_TOOLCHAIN_FILE=%s" % self._toolchain)
            if self._extra_args:
                cmake_args.append(self._extra_args)

            run_command("%s %s" % (" ".join(args), " ".join(cmake_args)), cwd=self._build_dir)
        except:
            print "##teamcity[buildProblem description='cmake generate error: %s']" % (escape_teamcity_message(sys.exc_info()[1]))
            raise

    def build(self, target = None, args = None):
        try:
            print "cmake %s target %s args %s" % (self, target, args)
            if target and isinstance(target, basestring):
                target = [target]
            if args is None: args = []

            if self._generator.startswith("Visual Studio"):
                raise NotImplementedError
            elif self._generator == "Xcode":
                jobs = self._build_concurrency if self._build_concurrency else multiprocessing.cpu_count()
                args.append("xcodebuild")
                args.append("-parallelizeTargets")
                args.append("-jobs %d" % jobs)
                args.append("-configuration %s" % self._configuration)
                if target:
                    for t in target:
                        args.append("-target %s" % t)
                run_command(" ".join(args), cwd=self._build_dir)
            elif self._generator == "Unix Makefiles":
                jobs = self._build_concurrency if self._build_concurrency else multiprocessing.cpu_count()
                args.append("make")
                args.append("VERBOSE=1")
                args.append("-j%d" % jobs)
                if target:
                    for t in target:
                        args.append(t)
                run_command(" ".join(args), cwd=self._build_dir)
            elif self._generator == "Ninja":
                args.append("ninja")
                args.append("-v")
                # Let ninja decide on concurrency if it was not provided.
                if self._build_concurrency:
                    args.append("-j%d" % self._build_concurrency)
                if target:
                    for t in target:
                        args.append(t)
                run_command(" ".join(args), cwd=self._build_dir)
            else:
                raise NotImplementedError
        except:
            print "##teamcity[buildProblem description='cmake build error: %s']" % (escape_teamcity_message(sys.exc_info()[1]))
            raise

    def test(self):
        try:
            args = []
            args.append("-C %s" % self._configuration)
            args.append("-VV")
            args.append("--output-on-failure")
            if self._test_parallelize:
                 args.append("-j %d" % multiprocessing.cpu_count())
            if self._test_filter:
                 args.append("-R %s" % self._test_filter)
            run_command("ctest %s" % " ".join(args), cwd=self._build_dir)
        except:
            print "##teamcity[buildProblem description='error running tests: %s']" % (escape_teamcity_message(sys.exc_info()[1]))
            raise

    def analyze(self):
        try:
            analyzer_args = []
            analyzer_args.append("-DCMAKE_C_COMPILER=ccc-analyzer")
            analyzer_args.append("-DCMAKE_CXX_COMPILER=c++-analyzer")

            gen_args = []
            gen_args.append("scan-build")
            self.generate(args=gen_args,cmake_args=analyzer_args)

            build_args = []
            build_args.append("scan-build")
            build_args.append("-o %s" % (os.path.join(self._build_dir, "scan-build-results")))
            self.build(args=build_args)
        except:
            print "##teamcity[buildProblem description='error running analyzer: %s']" % (escape_teamcity_message(sys.exc_info()[1]))
            raise

class CommandCmake:
    @staticmethod
    def description():
        return "Run CMake, build targets and run tests"

    @staticmethod
    def options(parser, defaults):
        g = parser.add_argument_group("Build stages")
        g.add_argument("--clean",
                        help="Clean the build folder before anything else",
                        action="store", nargs="?", type=str2bool, const=True, default=False)
        g.add_argument("--generate",
                        help="Generate project file",
                        action="store", nargs="?", type=str2bool, const=True, default=True)
        g.add_argument("--build",
                        help="Build targets",
                        action="store", nargs="?", type=str2bool, const=True, default=True)
        g.add_argument("--test",
                        help="Run tests with ctest",
                        action="store", nargs="?", type=str2bool, const=True, default=True)
        g.add_argument("--package",
                        help="Package the client",
                        action="store", nargs="?", type=str2bool, const=True, default=False)

        g = parser.add_argument_group("Features")
        g.add_argument("--ccache",
                        help="Enable ccache",
                        action="store", nargs="?", type=str2bool, const=True, default=False)
        g.add_argument("--sccache",
                        help="Enable sccache",
                        action="store", nargs="?", type=str2bool, const=True, default=False)
        g.add_argument("--sccache-directory",
                        help="Directory to use for caching",
                        action="store", default=argparse.SUPPRESS)
        g.add_argument("--sccache-gcs-warden-url",
                        help="URL to gcs-warden service for fetching GCS credentials",
                        action="store", default=argparse.SUPPRESS)
        g.add_argument("--sccache-gcs-bucket",
                        help="GCS bucket to use for caching",
                        action="store", default=argparse.SUPPRESS)
        g.add_argument("--sccache-gcs-period",
                        help="Required GCS bucket access period",
                        action="store", nargs=1, default=argparse.SUPPRESS)
        g.add_argument("--unity",
                        help="Enable unity builds",
                        action="store", nargs="?", type=str2bool, const=True, default=False)
        g.add_argument("--sanitizer",
                        help="Use a build sanitizer",
                        choices=['address','thread','memory','undefined','safe-stack', 'leak'],
                        nargs="?")
        g.add_argument("--analyze",
                        help="Perform a scan-build analysis",
                        action="store", nargs="?", type=str2bool, const=True, default=False)

        g = parser.add_argument_group("Advanced options")
        g.add_argument("--target",
                        help="Target to build, can be repeated",
                        action=ExtendAction)
        g.add_argument("--post-target",
                        help="Target to build after normal targets and tests, can be repeated",
                        action=ExtendAction)
        g.add_argument("--cmake-generator",
                        help="CMake generator",
                        choices=['Xcode', 'Ninja', 'Unix Makefiles', 'Visual Studio 15 2017'])
        g.add_argument("--configuration",
                        help="Build configuration",
                        choices=['Debug', 'Release', 'Coverage'])
        g.add_argument("--build-dir",
                        help="Build directory",
                        type=os.path.abspath)
        g.add_argument("--build-concurrency",
                        help="Build concurrency",
                        type=int,
                        default=argparse.SUPPRESS)
        g.add_argument("--test-parallelize",
                        help="Run tests in parallel",
                        action="store",
                        type=str2bool,
                        default=True)
        g.add_argument("--test-filter",
                        help="Test filter regexp",
                        action="store")
        g.add_argument("--extra-cmake",
                        help="Extra CMake arguments, can be repeated",
                        action=ExtendAction,
                        default=[])
        g.add_argument("--toolchain",
                        help="Set custom cmake toolchain file",
                        action="store")
        g.add_argument("--arch",
                        help="Set architecture to build for",
                        action="store")

    @staticmethod
    def run(options):
        if options.clean and os.path.isdir(options.build_dir):
            shutil.rmtree(options.build_dir)
        if not os.path.isdir(options.build_dir):
            os.makedirs(options.build_dir)

        other_args = {}

        with log_section("Downloading tools"):
            try:
                find_software("cmake").setup(options)

                if options.cmake_generator == "Ninja":
                    find_software("ninja").setup(options)

                find_software("node").setup(options)

                if options.platform == "windows":
                    find_software("visualstudio").setup(options)
                elif options.platform == "osx" or options.platform == "ios":
                    find_software("xcode").setup(options)
                elif options.platform == 'linux':
                    find_software('clang').setup(options)
                    find_software('apt').setup(options)
                elif options.platform == 'android':
                    find_software('android_ndk').setup(options)
                else:
                    raise NotImplementedError

                if options.sanitizer and options.platform != 'android':
                    find_software('clang').setup(options)

                if options.analyze:
                    find_software('checker').setup(options)

                if options.ccache:
                    find_software("ccache").setup(options)

                if options.sccache:
                    sccache_bin = find_software("sccache").setup(options)
                    options.extra_cmake.append("-DCMAKE_C_COMPILER_LAUNCHER=%s" % sccache_bin)
                    options.extra_cmake.append("-DCMAKE_CXX_COMPILER_LAUNCHER=%s" % sccache_bin)
            except:
                print "##teamcity[buildProblem description='error downloading tools: %s']" % (escape_teamcity_message(sys.exc_info()[1]))
                raise

        if options.toolchain:
            other_args['toolchain'] = options.toolchain

        if options.unity:
            options.extra_cmake.append("-DUNITY_BUILD=ON")

        if options.sanitizer:
            if 'address' in options.sanitizer:
                options.extra_cmake.append("-DUSE_ADDRESS_SANITIZER=ON")
            if 'thread' in options.sanitizer:
                options.extra_cmake.append("-DUSE_THREAD_SANITIZER=ON")
            if 'memory' in options.sanitizer:
                options.extra_cmake.append("-DUSE_MEMORY_SANITIZER=ON")
            if 'undefined' in options.sanitizer:
                options.extra_cmake.append("-DUSE_UNDEF_BEHAVIOUR_SANITIZER=ON")
            if 'safe-stack' in options.sanitizer:
                options.extra_cmake.append("-DUSE_SAFE_STACK_SANITIZER=ON")
            if 'leak' in options.sanitizer:
                options.extra_cmake.append("-DUSE_LEAK_SANITIZER=ON")

        # Merge all extra cmake arguments
        extra_args = " ".join(options.extra_cmake) if options.extra_cmake else None

        cmake = CMake(build_dir=options.build_dir,
                      build_concurrency=options.build_concurrency if 'build_concurrency' in options else None,
                      configuration=options.configuration,
                      generator=options.cmake_generator,
                      test_parallelize=options.test_parallelize,
                      test_filter=options.test_filter,
                      extra_args=extra_args,
                      **other_args)

        if options.generate:
            with log_section("Generating CMake"):
                cmake.generate()

        if options.build:
            with log_section("Build"):
                print "Building target: %s" % (options.target or "default")
                cmake.build(target=options.target)

        if options.test:
            with log_section("Test"):
                cmake.test()

        if options.build and options.post_target:
            with log_section("Post build"):
                print "Building post-build target: %s" % (options.post_target)
                cmake.build(target=options.post_target)

        if options.analyze:
            with log_section("Analyze"):
                cmake.analyze()

        if options.package:
            with log_section("Packaging"):
                if 'package_action' in options:
                    options.package_action(cmake, options)
                else:
                    cmake.build(target="package_installer")

