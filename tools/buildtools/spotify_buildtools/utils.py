import argparse
import collections
import importlib
import os
import subprocess
from contextlib import contextmanager

# Convenience function to add a path to the PATH environment variable
def prepend_path(path):
    os.environ['PATH'] =  path + os.pathsep + os.environ['PATH']

# Print command, run it, raise exception on failure
# cwd defaults to the current program cwd is not set
def run_command(cmd, cwd=None):
    if not cwd:
        cwd = os.getcwd()

    print "Running command: %s" % cmd
    p = subprocess.Popen(cmd, shell=True, cwd=cwd)
    p.wait()
    if p.returncode != 0:
        raise Exception("Command %s returned error code %d" % (cmd, p.returncode))

# Convert a string to a boolean value
# Conversion is not case sensitive and raises an error if it fails
# Mainly targeted for the "type" parameter argparse add_argument
# true on t 1 => True
# false off f 0 => False
def str2bool(string):
    string = string.lower()
    if string in ['true', 'on', 't', '1']:
        return True
    if string in ['false', 'off', 'f', '0']:
        return False
    raise Exception("Can't convert %s to boolean" % string)

# argparse default append action appens arguments to the default value
# and the default value can not be removed
# This action replaces the default value and appends more values if the
# argument is used multiple times
class ExtendAction(argparse.Action):
    def __init__(self, *args, **kwargs):
        super(ExtendAction, self).__init__(*args, **kwargs)
        if self.default and not isinstance(self.default, list):
            self.default = [self.default]
        self.reset_dest = False
    def __call__(self, parser, namespace, values, option_string=None):
        if not self.reset_dest:
            setattr(namespace, self.dest, [])
            self.reset_dest = True
        dest = getattr(namespace, self.dest)
        if not isinstance(values, basestring):
            dest.extend(values)
        else:
            dest.append(values)

# Convenience function to load a software installer
def find_software(name):
    print "Installing %s" % name
    return importlib.import_module("spotify_buildtools.software.%s" % name)

# Write a message to stdout
# If the program is running within TeamCity, it will create a block section
# that can be expanded or fold with the message as header
# Should be use like this:
# with log_section('Compile'):
#     compile()
@contextmanager
def log_section(message):
    def escape(text):
        quote = {
            "'": "|'",
            "|": "||",
            "\n": "|n",
            "\r": "|r",
            '[': '|[',
            ']': '|]',
        }
        return "".join([quote.get(x, x) for x in text])

    if 'TEAMCITY_VERSION' in os.environ:
        print "\n##teamcity[blockOpened name='%s']" % escape(message)
    print message
    try:
        yield message
    finally:
        if 'TEAMCITY_VERSION' in os.environ:
            print "\n##teamcity[blockClosed name='%s']" % escape(message)
