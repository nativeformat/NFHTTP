import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb
import errno
import platform
from os import path, listdir, chdir, getcwd, mkdir, makedirs, environ
from re import compile as regex
from shutil import rmtree

node_pkg_re = regex(r"node-v[0-9\.]+")
node_search_paths = ("node", "bin", node_pkg_re)

def match_str(re_or_str, value):
    try:
        if re_or_str.match(value) is not None:
            return True
    except AttributeError:
        if re_or_str == value:
            return True
    return False

def find_node_bin(spath):
    for f in listdir(spath):
        fpath = path.join(spath, f)
        if path.isdir(fpath):
            for search in node_search_paths:
                if match_str(search, f):
                    return find_node_bin(fpath)
    return spath

def require_app(parent_dir, app):
    if not (path.isfile(path.join(parent_dir, app)) or
            path.isfile(path.join(parent_dir, app + ".exe"))):
        raise Exception("Couldn't find %s executable in %s" % (app, parent_dir))

def setup(options, **kwargs):
    if options.platform == "linux" and platform.architecture()[0] == '32bit':
        print "Skipping install on 32bit Linux"
        return
    print "Setup Node. Options: %s" % options
    node_output = sb.SoftwareBase('node').install(options)
    if not node_output:
        raise Exception("Node install path not found, check vulcan configs")

    base_dir = find_node_bin(node_output)
    require_app(base_dir, "node")
    require_app(base_dir, "npm")
    utils.prepend_path(base_dir)

    # Unresolved NPM issue on Windows requires installing an arbitrary package globally in order to
    # create a required directory which is not actually used by us, since we only perform local
    # installations.
    # https://github.com/joyent/node/issues/8141
    #
    # because we do not want to install anything on the machine we just create the path
    if options.platform == "windows":
        # ensure nothing lingers on the platform
        npm_global_cache_path = path.join(environ['APPDATA'], 'npm-cache')

        try:
            rmtree(npm_global_cache_path)
        except:
            pass

        try:
            makedirs(npm_global_cache_path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
