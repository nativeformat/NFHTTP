import sys
import argparse
import spotify_buildtools.utils as utils

class CommandPreset:
    presets = []

    @staticmethod
    def set_presets(presets):
        CommandPreset.presets = presets

    @staticmethod
    def description():
        return "Run preset commands"

    @staticmethod
    def options(parser, defaults):
        for k, v in sorted(CommandPreset.presets.iteritems()):
            parser.add_argument("--%s" % k, dest="presets", help=v["description"], action="append_const", const=k, default=argparse.SUPPRESS)

    @staticmethod
    def run(options):
        if not options.presets:
            raise Exception("Missing preset to build. Check the help to see which are available.")
        print "Presets: %s" % options.presets
        for p in options.presets:
            args = [sys.executable, sys.argv[0]]
            args.extend(CommandPreset.presets[p]["command"].split())
            utils.run_command(" ".join(args))

