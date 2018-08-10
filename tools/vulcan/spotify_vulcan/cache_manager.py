import os
import sys
import shutil
import hashlib
import logging
import requests
import operator
import urlparse
import collections
import tempfile
import time

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import read_json_file, read_definitions_array, select_dependencies, detect_os
from utils import del_ro


def setup_log(logs_path):
    from time import gmtime, strftime

    if not logs_path:
        logs_path = root_path

    log_dir = os.path.join(logs_path, 'logs', strftime("%Y-%m-%d_%H.%M.%S", gmtime()))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(os.path.join(log_dir, '%s.log' % (__name__)))
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    if os.environ.get('TEAMCITY_VERSION') is not None:
        # create console handler tasked with writing
        # exceptions on teamcity format
        th = logging.StreamHandler()
        th.setLevel(logging.ERROR)

        # create teamcity formatter
        tc_formatter = TeamCityFormatter("%(name)s - %(message)s")
        th.setFormatter(tc_formatter)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the self.logger if we hadn't done it before.
    if len(logger.handlers) == 0:
        logger.addHandler(fh)
        logger.addHandler(ch)
        if os.environ.get('TEAMCITY_VERSION') is not None:
            logger.addHandler(th)

    return logger


class TeamCityFormatter(logging.Formatter):
    quote = {"'": "|'", "|": "||", "\n": "|n", "\r": "|r", ']': '|]',
             '[': '|[', u"\u0085": '|x', u"\u2028": '|l', u"\u2029": '|p'}

    def format(self, record):
        pre_esc_string = super(TeamCityFormatter, self).format(record)
        return "##teamcity[buildProblem description='" + \
            self.tc_msg_escape(pre_esc_string) + "']"

    def tc_msg_escape(self, msg):
        return "".join([self.quote.get(x, x) for x in msg])


class CacheManager(object):
    class CannotFreeSpaceError(BaseException):
        pass

    ntuple_diskusage = collections.namedtuple('usage', 'total used free')
    ntuple_artifacts = collections.namedtuple('artifacts_sorted', 'artifact_path last_accessed')

    def __init__(self, vulcan_file, vulcan_folder=os.path.join(os.path.expanduser("~"), ".vulcan"), properties={}, filters={}, do_logging=True, logs_path=root_path, option_target_free_space_string=None):
        self.logger = setup_log(logs_path) if do_logging else logging.getLogger('dummy')
        self.path_to_cache = os.path.join(vulcan_folder, "cache")
        self.vulcan_file = vulcan_file
        self.filters = filters
        self.properties = properties

        if not os.path.exists(self.path_to_cache):
            os.makedirs(self.path_to_cache)
            self.logger.debug("Created cache directory: %s " % self.path_to_cache)

        self.delete_remains()

        self.artifacts_urls, self.artifacts_dirs, vulcan_file_target_free_space_string, self.unpacked_multiplier_guestimate, self.cur_artifact_url = self.read_vulcan_file()
        target_free_space_string = "2G"  # 2 GB free space as default
        if option_target_free_space_string is not None:
            target_free_space_string = option_target_free_space_string
        elif vulcan_file_target_free_space_string is not None:
            target_free_space_string = vulcan_file_target_free_space_string
        self.target_free_space = self.get_bytes_from_size_string(target_free_space_string)

        self.logger.debug('CacheManager will try to keep %s (%s B) free',
                         target_free_space_string, self.target_free_space)

        self.logger.debug('Current artefact url: %s', self.cur_artifact_url)
        self.logger.debug('CacheManager created.\nvulcan_file=%s,\nvulcan_folder=%s,\ncache_folder=%s,\nartifacts_urls:\n%s,\nartifacts_dirs:\n%s,\ntarget_free_space=%s,\nmultiplier=%s' % (vulcan_file, vulcan_folder, self.path_to_cache, '\n  '.join(self.artifacts_urls), '\n  '.join(self.artifacts_dirs), self.target_free_space, self.unpacked_multiplier_guestimate,))

    def read_vulcan_file(self):
        vulcan_file_json = read_json_file(self.vulcan_file)
        target_free_space = vulcan_file_json.get('target_free_space')
        unpacked_multiplier_guestimate = vulcan_file_json['unpacked_artifacts_multiplier_guestimate'] if vulcan_file_json.get('unpacked_artifacts_multiplier_guestimate') else 2 # factor of 2 as default

        dependencies = vulcan_file_json['dependencies']
        defs = read_definitions_array(dependencies)

        if 'current_os' not in self.properties:
            self.properties['current_os'] = detect_os()
        self.essential_dependencies = select_dependencies(self.properties, {}, {}, *defs).values()
        self.current_dependency = select_dependencies(self.properties, self.filters, {}, *defs).values()

        artifacts_urls = [dep[0].load_value('url') for dep in self.essential_dependencies]
        artifacts_dirs = [os.path.join(self.path_to_cache, self.url_to_dirname(url)) for url in artifacts_urls]
        cur_artifact_url = [dep[0].load_value('url') for dep in self.current_dependency]

        return artifacts_urls, artifacts_dirs, target_free_space, unpacked_multiplier_guestimate, cur_artifact_url

    @staticmethod
    def get_bytes_from_size_string(sstring):
        if sstring is None:
            return

        suffixes = (('k', 1024),
                    ('m', 1024**2),
                    ('g', 1024**3),
                    ('t', 1024**4))

        trimmed = sstring.replace(" ", "").strip().lower()
        for s, n in suffixes:
            if s in trimmed:
                return n * int(trimmed[:-1])
        else:
            return int(trimmed)

    @staticmethod
    def disk_usage(path=os.getcwd()):

        if hasattr(os, 'statvfs'):  # POSIX
                st = os.statvfs(path)
                free = st.f_bavail * st.f_frsize
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize
                return CacheManager.ntuple_diskusage(total, used, free)

        elif os.name == 'nt':       # Windows
            import ctypes
            import sys

            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                ctypes.c_ulonglong()
            if sys.version_info >= (3,) or isinstance(path, unicode):
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            else:
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
            ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
            if ret == 0:
                raise ctypes.WinError()
            used = total.value - free.value
            return CacheManager.ntuple_diskusage(total.value, used, free.value)
        else:
            raise NotImplementedError("platform not supported")

    def _get_artifacts_in_path(self):
        return [os.path.join(self.path_to_cache, artifact) for artifact in os.walk(self.path_to_cache).next()[1]]

    def _get_last_accessed(self, path_to_dir):
            metadata = os.path.join(path_to_dir, "metadata.json")
            if os.path.exists(metadata):
                return read_json_file(metadata)["last-used"]

            # No metadata file, return the modification time of the folder
            return os.path.getmtime(path_to_dir)

    def _get_free_space(self):
        return CacheManager.disk_usage(self.path_to_cache).free

    def get_sorted_artifacts(self):
        # Using date of last_accessed as primary key and size as secondary key.
        # If no metadata.json is found in the artifact's directory, will use last access time on a random file in dir.

        artifacts = []
        artifacts_paths = self._get_artifacts_in_path()
        for artifact in artifacts_paths:
            artifacts.append(CacheManager.ntuple_artifacts(artifact, self._get_last_accessed(artifact)))

        artifacts = sorted(artifacts, key=operator.attrgetter('last_accessed'))

        return artifacts

    def delete_remains(self):
        for artifact in self._get_artifacts_in_path():
            if artifact.endswith(".delete"):
                try:
                    self.logger.info("Deleting old artifact %s", artifact)
                    delete_path = tempfile.mktemp(suffix='.delete', dir=os.path.dirname(artifact))
                    os.rename(artifact, delete_path)
                    shutil.rmtree(delete_path, onerror=del_ro)
                except:
                    self.logger.debug('Failed to delete artifact %s', artifact)

    def url_to_dirname(self, url):
        sha = hashlib.sha1()
        sha.update(url)
        hash = sha.hexdigest()

        parsed_url = urlparse.urlparse(url)
        basename = os.path.basename(parsed_url.path)
        return '%s-%s' % (basename, hash,)

    def http_get(self, url, auth, max_retries=0, retry_for_status_codes=None,
                 backoff_factor=0.2, get_method=requests.get):
        """GET an URL, with optional retry on specified HTTP status codes.

        :param url: URL to get response from
        :param auth: Authentication information
        :param max_retries: Number of retries
        :param retry_for_status_codes: Iterable of int HTTP status codes that
                                       will trigger a retry
        :param backoff_factor: Base for exponential backoff in seconds
        :param get_method: method to use for http get method. Must be compatible
                           with requests.get
        :return: The response
        """

        for retry in xrange(max_retries + 1):
            # Check connection errors
            try:
                response = get_method(url, stream=True, auth=auth)
            except requests.exceptions.ConnectionError as e:
                self.logger.error("Can't connect to %s", url)
                raise e
            except requests.exceptions.ConnectTimeout as e:
                self.logger.error("Connection to %s timed out!", url)
                raise e

            if response.status_code in retry_for_status_codes and \
               retry < max_retries:
                sleep = backoff_factor * (2 ** retry)
                self.logger.info("Got HTTP status code %d (attempt %d). Will "
                                 "retry in %.2f s", response.status_code,
                                 retry + 1, sleep)
                time.sleep(sleep)
                continue

            # Check for HTTP Errors
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                self.logger.error("Got HTTP Error for url %s: %s", url, e.message)
                raise e

            return response

    def query_essential_artifacts_size(self):
        artifacts_size = 0
        auth = requests.auth.HTTPBasicAuth('teamcity', 'Leahie6ji9')
        for url in self.cur_artifact_url:
            if url.startswith("https://artifactory.spotify.net"):
                full_url = url.replace('/artifactory/', '/artifactory/api/storage/')
                dirname = os.path.join(self.path_to_cache, self.url_to_dirname(url))
                self.logger.debug('Checking build dependency for existence %s', dirname)
                if not (os.path.exists(dirname) and os.path.exists(os.path.join(dirname, 'extracted'))):
                    self.logger.debug('Querying artifactory for size of %s' % (url,))

                    # IOS-10379: Retry on HTTP status code 504 from
                    # Artifactory API
                    response = self.http_get(full_url, auth=auth, max_retries=3,
                                             retry_for_status_codes=(500, 504))

                    try:
                        response_json = response.json()
                    except Exception as e:
                        self.logger.error("Could not decode response %s to json.", response.text)
                        raise e

                    try:
                        size = response_json['size']
                    except KeyError as e:
                        self.logger.error("Size not found in returned json. Json: %s", response_json)
                        raise e

                    try:
                        artifacts_size += int(size)
                    except ValueError as e:
                        self.logger.error("Returned size not a valid number! Json: %s", response_json)
                        raise e
        return artifacts_size

    def free_space_for_artifacts(self):
        artifacts_size = self.query_essential_artifacts_size()
        target_free_space = artifacts_size * (self.unpacked_multiplier_guestimate + 1)
        self.logger.debug('Freeing space for artifacts. artifacts_size=%s, target_free_space=%s' % (artifacts_size, target_free_space,))
        self._free_space(target_free_space)

    def free_space_after_fetching_dependencies(self):
        self.logger.debug('Freeing space after fetching dependencies. target_free_space=%s' % (self.target_free_space,))
        self._free_space(self.target_free_space)

    def _free_space(self, target_free_space):
        current_free_space = self._get_free_space()
        artifact_sorted_for_deletion = [ar.artifact_path for ar in self.get_sorted_artifacts() if ar.artifact_path not in self.artifacts_dirs]
        self.logger.debug('Artifacts sorted for deletion:\n %s' % ('\n'.join(artifact_sorted_for_deletion),))
        self.logger.debug('Free space prior deletion: %s' % (current_free_space,))
        while current_free_space < target_free_space:
            if len(artifact_sorted_for_deletion) == 0:
                self.logger.error("Can't free enough space from cache to reach target space. Raising...")
                raise CacheManager.CannotFreeSpaceError("Can't clean enough space from cache")

            artifact_to_delete = artifact_sorted_for_deletion.pop(0)
            self.logger.info('deleting artifact %s' % (artifact_to_delete,))
            delete_path = tempfile.mktemp(suffix='.delete', dir=os.path.dirname(artifact_to_delete))
            os.rename(artifact_to_delete, delete_path)  # atomic delete (if app crashes before it is done deleting, it will delete remains - all folders that end with '.delete' - on next run
            shutil.rmtree(delete_path)

            current_free_space = self._get_free_space()
            self.logger.debug('Free space after deletion: %s' % (current_free_space,))
        self.logger.debug('Done freeing space.')
