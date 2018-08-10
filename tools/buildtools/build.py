#!/usr/bin/python
import os
import sys
import subprocess

from options import Target
from options import Options


class BuildtoolsTarget(Target):
    '''
    This target builds the buildtools.
    '''

    def name(self):
        return 'buildtools'

    def description(self):
        return 'Builds the buildtools using the buildtools, ;)'

    def is_default(self):
        return True

    def test(self, line):
        for file in ['options_test.py']:
            status = subprocess.call(['python', file])
            if status:
                raise Exception('%s: tests failed' % file)

options = Options()
options.parameters += (BuildtoolsTarget(),)
line = options.do(*sys.argv)
line.info("Build successful")
