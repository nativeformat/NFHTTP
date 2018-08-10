from spotify_buildtools.utils import run_command
from spotify_buildtools.utils import find_software

class CommandRun:
    @staticmethod
    def description():
        return "Run command, optionally install programs"

    @staticmethod
    def options(parser, defaults):
        parser.add_argument("--install", action='append', help='Install software by name, possibly comma separated values', default=[])
        parser.add_argument("--arch", action='store', help='Target build architecture', default='')
        parser.add_argument("--command", action='append', nargs='+', dest='run_command', help='Command to run', required=True)

    @staticmethod
    def run(options):
        if options.install:
            for installlist in options.install:
                for s in installlist.split(","):
                    find_software(s).setup(options) 

        for c in options.run_command:
            run_command(" ".join(c))
