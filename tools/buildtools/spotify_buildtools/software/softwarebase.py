import os
import re
import subprocess
import sys

class SoftwareBase:
    @staticmethod
    def _vulcan_set_path():
        if 'VULCAN_FOLDER' not in os.environ:
            home_folder = os.environ.get('HOME')
            if home_folder is None:
                home_folder = os.path.expanduser('~')
            # HOME is set to a dummy value by sbuild
            # So let's store the cache in the current folder
            if not os.path.isdir(home_folder):
                home_folder = os.getcwd()
            vulcan_folder = os.path.join(home_folder, '.vulcan')
            os.environ['VULCAN_FOLDER'] = vulcan_folder

    @staticmethod
    def _vulcan_locate():
        vulcan_paths = [
            'vulcan/bin/vulcan.py',
            'vendor/vulcan/bin/vulcan.py'
        ]
        if 'VULCAN_PATH' in os.environ:
            vulcan_paths.insert(0, os.environ['VULCAN_PATH'])
        try:
            return os.path.normpath(next(iter(filter(os.path.isfile, vulcan_paths)), None))
        except:
            raise Exception('''Couldn't find vulcan in any of %s %s''' % (os.getcwd(), vulcan_paths))

    @staticmethod
    def _vulcan_run(filename, target):
        SoftwareBase._vulcan_set_path()
        vulcan_bin = SoftwareBase._vulcan_locate()

        cmd = [sys.executable, vulcan_bin, '-f', filename, '-p', target, '-i', 'id=%s' % target]
        output = subprocess.check_output(cmd).strip()
        return output

    @staticmethod
    def _vulcan_list(filename):
        vulcan_bin = SoftwareBase._vulcan_locate()
        cmd = [sys.executable, vulcan_bin, '-f', filename, '--list']
        output = [l.strip() for l in subprocess.check_output(cmd).strip().split("\n")]
        return output

    def __init__(self, name):
        self._name = name

    def _vulcan_get_filename(self):
        return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '%s.vulcan' % self._name))

    def list(self):
        return SoftwareBase._vulcan_list(self._vulcan_get_filename())

    # Installs either the version specified in toolname-version or the package with the same
    # name as the tool or the first one in the list
    def install(self, options):
        localpath = getattr(options, '%s-path' % self._name, None)
        if localpath:
            print "Using %s from local path: %s" % (self._name, localpath)
            return localpath

        # See: https://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
        def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split(_nsre, s)]

        versions = sorted(self.list(), key=natural_sort_key, reverse=True)
        if not len(versions):
            raise Exception("Can't find any installable software for %s" % self._name)

        version = getattr(options, '%s-version' % self._name, None)
        target = self._name if self._name in versions else versions[0]
        if version:
            target = '%s-%s' % (self._name, version)
        if not target in versions:
            raise Exception("Can't find software %s version %s (available: %s)" % (self._name, version, versions))

        return SoftwareBase._vulcan_run(self._vulcan_get_filename(), target)
