import argparse
import os
import platform
import sys
import time

import spotify_buildtools.schroot as schroot

# Reopen stdout as unbuffered
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

def host_platform():
    host = platform.system().lower()
    if host == 'darwin':
        return 'osx'
    return host

# Show help for all sub-parsers
class _HelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        print(parser.format_help())

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("==== Command '{}' ====".format(choice))
                print(subparser.format_help())

        parser.exit()

def parse(commands, defaults, platform_defaults, description=None, arguments=None):
    if not arguments:
        arguments = sys.argv

    # create the top-level parser
    parser = argparse.ArgumentParser(prog='PROG', add_help=False)  # here we turn off default help action
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter, add_help=False)
    parser.add_argument('--platform', nargs='?', default=host_platform(), choices=defaults['available_platforms'], help='Platform to build')
    if host_platform() == 'linux':
        parser.add_argument('--schroot-name', action='store', help='Schroot name to use')
        parser.add_argument('--schroot-root-port', action='store', type=int, help=argparse.SUPPRESS)
        parser.add_argument('--schroot-root-agent', action='store_true', help=argparse.SUPPRESS)

    # Check the platform that is requested and update defaults values
    options, remaining_args = parser.parse_known_args()

    # Do chroot work now
    if 'schroot_name' in options and options.schroot_name:
        schroot.create(options, remaining_args)

    if 'schroot_root_port' in options and options.schroot_root_agent:
        schroot.root_agent()

    if 'schroot_root_agent' in options and options.schroot_root_port:
        schroot.connect_root_agent(options.schroot_root_port)

    for key, v in platform_defaults.get(options.platform, {}).iteritems():
        key = key.lower()
        defaults.setdefault(key, {}).update(platform_defaults[options.platform][key])

    # Add other commands
    parser.add_argument('--help', '-h', action=_HelpAction)  # add custom help
    sub = parser.add_subparsers(title='subcommands', help="Pick a command to run")
    for command, clazz in commands.iteritems():
        command_parser = sub.add_parser(command, add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter, help=clazz.description())
        clazz.options(command_parser, options)
        command_parser.set_defaults(command=clazz.run, **defaults.get(command, {}))

        # Patch the choices with default values taken from %option_name%_choices
        for a in command_parser._actions:
            if a.dest + "_choices" in defaults.get(command, {}):
                a.choices = defaults[command][a.dest + "_choices"]

    # Parse options and run the command!
    options = parser.parse_args(remaining_args, options)
    options.command(options)
