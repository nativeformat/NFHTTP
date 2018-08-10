import os
import sys
import spotify_buildtools.utils as utils

class CommandCpplint:
    @staticmethod
    def description():
        return "Run cpplint over all the files"

    @staticmethod
    def options(parser, defaults):
        parser.add_argument("file", nargs='?', help="Output file")

    @staticmethod
    def run(options):
        cpplintgraph_paths = [
            "scripts/cpplint/cpplintgraph.py",
            "other/scripts/cpplintgraph.py",
        ]
        cpplintgraph = os.path.normpath(next(iter(filter(os.path.isfile, cpplintgraph_paths)), None))

        args = [sys.executable, cpplintgraph]
        if options.file:
            args.append(options.file)

        os.environ['PYTHONPATH'] = os.pathsep.join(["infra/other/scripts", "other/scripts"])
        utils.run_command(" ".join(args))
