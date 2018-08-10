import errno
import glob
import hashlib
import json
import os
import requests
import shutil
import subprocess
import sys
import time
import tarfile
import urlparse
import zipfile
import socket
from contextlib import closing

from requests.auth import HTTPBasicAuth


class UrlAssembler(object):

    def __init__(self, dependency):
        self.dependency = dependency
        self.url = dependency.load_value('url')
        self.action = self.dependency.get_string_value('action', 'extract')
        self.format = dependency.get_string_value('format', 'auto')
        self.parsed_url = urlparse.urlparse(self.url)
        if self.action in ('extract', 'manage') and self.format == 'auto':
            path = self.parsed_url.path
            if path.endswith('.zip'):
                self.format = 'zip'
            elif path.endswith('.tar'):
                self.format = 'tar'
            elif path.endswith('.tar.gz') or path.endswith(".tgz"):
                self.format = 'tar.gz'
            elif path.endswith('.tar.bz2'):
                self.format = 'tar.bz2'
            else:
                raise RuntimeError('unknown format "%s"' % self.format)

    def filename(self):
        sha = hashlib.sha1()
        sha.update(self.url)
        hash = sha.hexdigest()
        basename = os.path.basename(self.parsed_url.path)
        return '%s-%s/%s' % (basename, hash, basename)

    def fetch_file_wrap(self, filename, auth):
        # wrapper that measures the time taken to do the download
        start = time.time()
        response = self.fetch_file(filename, auth)
        duration = time.time() - start
        response_size = int(response.headers['content-length'])
        if duration > 2:
            # only log slow downloads
            # speed in MB/s because Bytes/second is silly
            speed = response_size / (1024 * 1024 * duration)
            addr = ('fastforwardbridge.spotify.net', 19000)

            # we want the filename without the /Users/name/.vulcan/ prefix
            payload = {
                "type": "metric",
                "key": "vulcan-cache-speed-MB",
                "value": speed,
                "attributes": {
                    "filename": self.filename(),
                    "host": socket.gethostname(),
                    "hostname": socket.gethostname(),
                    "url": self.url,
                    "speed_mb_sec": speed,
                    "size": response_size,
                    "duration": duration
                }
            }
            with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
                s.sendto(json.dumps(payload), addr)
        return response

    def fetch_file(self, filename, auth):
        if os.path.exists(filename):
            os.remove(filename)
        print >> sys.stderr, 'Downloading %s (%s)' % (self.url, filename)
        for i in range(5):
            try:
                response = requests.get(self.url, stream=True, auth=auth)
                response.raise_for_status()
                break
            except Exception as exc:
                print >> sys.stderr, 'Error while trying to download file: %s, retry %d out of 5' % (exc, i)
                saved_exc = exc
        else:
            raise saved_exc
        responsesize = int(response.headers['content-length'])
        print >> sys.stderr, 'File size: %s' % self.human_readable_size(responsesize)

        checksum_hexdigest = None
        checksum_hash = None

        # If a hash is present in the headers, hash the file as you read it
        if 'x-checksum-sha1' in response.headers:
            checksum_hexdigest = response.headers['x-checksum-sha1']
            checksum_hash = hashlib.sha1()
        elif 'x-checksum-md5' in response.headers:
            checksum_hexdigest = response.headers['x-checksum-md5']
            checksum_hash = hashlib.md5()

        # We report every 10% or 100MB
        report_chunk_size = min(responsesize / 10, 100 << 20)  # 100 MB
        report_size = 0
        report_target = report_chunk_size

        with open(filename + '.tmp', 'wb') as f:
            for chunk in response.iter_content(chunk_size=(1 << 20)):  # 1 MB
                if chunk:
                    f.write(chunk)
                    if checksum_hash:
                        checksum_hash.update(chunk)
                    report_size += len(chunk)
                    if report_size >= report_target:
                        report_target = report_size + report_chunk_size
                        print >> sys.stderr, 'Downloaded %s (%.2f %%)' % (self.human_readable_size(report_size),
                                                                          100.0 * report_size / responsesize)

        # Validate size read
        currentsize = os.path.getsize(filename + '.tmp')
        if currentsize != responsesize:
            os.remove(filename + '.tmp')
            raise RuntimeError('Download truncated')

        # Validate checksum
        if checksum_hash and checksum_hexdigest != checksum_hash.hexdigest():
            os.remove(filename + '.tmp')
            raise RuntimeError(
                'Checksum mismatch (actual %s, expected %s)' % (checksum_hexdigest, checksum_hash.hexdigest()))
        # Everything OK, move the tmp file to the right location
        os.rename(filename + '.tmp', filename)
        return response

    def ensure_dirname(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def download(self, filename, verbose=False):
        self.ensure_dirname(filename)

        artifactory = False
        auth = None
        if self.parsed_url.scheme == 'https' and self.parsed_url.hostname == 'artifactory.spotify.net':
            artifactory = True
            auth = HTTPBasicAuth('teamcity', 'Leahie6ji9')

        metadata_filename = os.path.join(os.path.dirname(filename), 'metadata.json')
        extracted_filename = os.path.join(os.path.dirname(filename), 'extracted')
        will_download = True
        response = None

        if os.path.exists(filename):
            if artifactory and self.dependency.get_bool_value('skip_cache_check'):
                return
            try:
                response = requests.head(self.url, auth=auth, timeout=5)
                response.raise_for_status()
            except Exception:
                print >> sys.stderr, 'HEAD query failed and file already exists, skipping verification'
                return
            # Simple file size check
            currentsize = os.path.getsize(filename)
            headsize = int(response.headers['content-length'])
            if currentsize != headsize:
                print >> sys.stderr, 'Local file is different, redownloading (local size=%d, remote size=%d)' % (currentsize, headsize)
                if os.path.exists(extracted_filename):
                    shutil.rmtree(extracted_filename)
            else:
                # Advanced metadata check against checksums
                metadata = {}
                if os.path.exists(metadata_filename):
                    with open(metadata_filename, 'rb') as metadata_file:
                        try:
                            metadata = json.load(metadata_file)
                        except:
                            pass
                if not 'sha1' in metadata and 'x-checksum-sha1' in response.headers:
                    # No metadata file, so sha1-hash it
                    digest = hashlib.sha1()
                    with open(filename, 'rb') as fd:
                        blocksize = 2**10
                        chunk = fd.read(blocksize)
                        while len(chunk) > 0:
                            digest.update(chunk)
                            chunk = fd.read(blocksize)
                    metadata['sha1'] = digest.hexdigest()
                # Match metadata against response headers
                if 'etag' in metadata and 'etag' in response.headers and metadata['etag'] != response.headers['etag']:
                    print >> sys.stderr, 'Local file is different, redownloading (local etag=%s, remote etag=%s)' % (metadata['etag'], response.headers['etag'])
                    if os.path.exists(extracted_filename):
                        shutil.rmtree(extracted_filename)
                elif 'sha1' in metadata and 'x-checksum-sha1' in response.headers and metadata['sha1'] != response.headers['x-checksum-sha1']:
                    print >> sys.stderr, 'Local file is different, redownloading (local sha1=%s, remote sha1=%s)' % (metadata['sha1'], response.headers['x-checksum-sha1'])
                    if os.path.exists(extracted_filename):
                        shutil.rmtree(extracted_filename)
                elif 'md5' in metadata and 'x-checksum-md5' in response.headers and metadata['md5'] != response.headers['x-checksum-md5']:
                    print >> sys.stderr, 'Local file is different, redownloading (local md5=%s, remote md5=%s)' % (metadata['md5'], response.headers['x-checksum-md5'])
                    if os.path.exists(extracted_filename):
                        shutil.rmtree(extracted_filename)
                elif len(glob.glob(os.path.join(extracted_filename, "._*"))) > 0:
                    print >> sys.stderr, 'Local file contains ._ files which means incorrect extraction'
                    shutil.rmtree(extracted_filename)
                    # We don't want to redownload, just extract again
                    will_download = False
                else:
                    # Everything passed, so don't redownload the file
                    will_download = False

        if will_download:
            response = self.fetch_file_wrap(filename, auth)

        # Generate and write metadata file
        metadata = {}
        metadata['url'] = self.url
        metadata['content-length'] = int(response.headers['content-length'])
        metadata['last-used'] = int(time.time())
        if 'etag' in response.headers:
            metadata['etag'] = response.headers['etag']
        if 'x-checksum-sha1' in response.headers:
            metadata['sha1'] = response.headers['x-checksum-sha1']
        if 'x-checksum-md5' in response.headers:
            metadata['md5'] = response.headers['x-checksum-md5']
        with open(metadata_filename, 'wb') as metadata_file:
            json.dump(metadata, metadata_file, indent=4, sort_keys=True)
            print >>metadata_file

    # This is needed to preserve executable bits on extracted files.
    # See: http://bugs.python.org/issue15795
    @staticmethod
    def system_unzip(zipfile, destination):
        try:
            subprocess.check_call(
                ['unzip', "-o", "-q", zipfile, "-d", destination])
        except OSError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        return True

    @staticmethod
    def python_unzip(filename, path):
        zf = None
        try:
            zf = zipfile.ZipFile(filename, 'r')
            #Due to windows being all crappy, we need to turn path into
            if sys.platform == "win32" or sys.platform == "win64":
                #explicit unicode path, to avoid 255 char path length limitation.
                path = '//?/' + path

                #Work around for zip-files with messed up path encodings so
                #zipfile doesn't get cranky.
                for zi in zf.infolist():
                  zi.filename = zi.filename.encode('cp437')

            zf.extractall(path)
        finally:
            if zf is not None:
                zf.close()

    @staticmethod
    def python_untar(filename, path, mode):
        def filter_files(tf):
            file_count = 0
            for tarinfo in tf:
                if os.path.basename(tarinfo.name).startswith("._"):
                    # Ignore ._* files in tar files
                    # Those are bad tar archives created from OSX without
                    # the option COPYFILE_DISABLE=1
                    continue
                file_count += 1
                if file_count % 5000 == 0:
                    print >> sys.stderr, "Extracted %d files..." % file_count
                yield tarinfo
        tf = None
        try:
            tf = tarfile.open(filename, mode)
            # Due to windows being all crappy, we need to turn path into...
            if sys.platform == "win32" or sys.platform == "win64":
                # ...an explicit unicode path, to avoid 255 char path length limitation.
                # Preflight the maximum path length needed for the extracted files
                contains_relative_path_items = False
                needs_unicode_path = False
                destination_base_length = len(path)
                for filename in tf.getnames():
                    if filename.startswith('./'):
                        contains_relative_path_items = True
                    if destination_base_length + len(filename) > 255:
                        # Non-unicode paths must be at most 255 characters long
                        needs_unicode_path = True
                        break

                if needs_unicode_path:
                    if contains_relative_path_items:
                        # Unicode paths must be absolute
                        print >> sys.stderr, 'tf.extractall(%s) will fail due to relative paths inside the tarfile!!!' % (path)
                    path = '//?/' + path

            tf.extractall(path, members=filter_files(tf))
        finally:
            if tf is not None:
                tf.close()

    def internal_extract(self, filename, path, verbose):
        if verbose:
            print >> sys.stderr, 'Extracting %s (%s)' % (path, filename)
        try:
            self.ensure_dirname(path)
            if self.format == 'zip':
                if not zipfile.is_zipfile(filename):
                    raise RuntimeError('file %s is not a zip file' % filename)
                if not UrlAssembler.system_unzip(filename, path):
                    UrlAssembler.python_unzip(filename, path)
            elif self.format == 'tar':
                if not tarfile.is_tarfile(filename):
                    raise RuntimeError('file %s is not a tar file' % filename)
                UrlAssembler.python_untar(filename, path, 'r')
            elif self.format in ('tar.gz', 'tar.bz2'):
                if not tarfile.is_tarfile(filename):
                    raise RuntimeError('file %s is not a tar file' % filename)
                mode = {'tar.gz': 'gz', 'tar.bz2': 'bz2'}[self.format]
                UrlAssembler.python_untar(filename, path, 'r:' + mode)
            else:
                raise RuntimeError('unknown format "%s"' % self.format)
        except:
            if os.path.isfile(filename):
                os.remove(filename)
            if os.path.isdir(path):
                shutil.rmtree(path)
            raise

    def extract(self, filename, path, verbose=False):
        # Create a temporary directory next to path
        tmp_path = path + ".tmp"
        if os.path.isdir(tmp_path):
            shutil.rmtree(tmp_path)
        os.makedirs(tmp_path)

        # extract() into there
        self.internal_extract(filename, tmp_path, verbose)

        # Rename the temp directory into path
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.rename(tmp_path, path)

    def manage(self, cache_dir, verbose=False):
        if self.dependency.get_load_value('path', fail=False):
            raise RuntimeError('"manage" is incompatible with "path",' +
                               ' please remove "path"')
        if self.dependency.get_load_value('package_id', fail=False):
            raise RuntimeError('"manage" is incompatible with "package_id",' +
                               ' please remove "package_id"')
        if self.dependency.get_load_value('check_package_id', fail=False):
            raise RuntimeError('"manage" is incompatible with' +
                               ' "check_package_id",' +
                               ' please remove "check_package_id"')
        filename = self.download_to_cache(cache_dir, verbose)
        extraction_path = self.extraction_path(cache_dir)
        #Since evil powers sometimes follow symlinks and deletes our extracted
        #resources, we need to check.
        try:
            is_empty = os.listdir(extraction_path) == []
        except OSError:
            #This means the directory does not exist
            pass
        if not os.path.isdir(extraction_path) or is_empty:
            self.extract(filename, extraction_path, verbose)
        link = self.dependency.get_value('link')
        if link:
            create = True
            if os.path.islink(link):
                linked = os.readlink(link)
                if linked == extraction_path:
                    create = False
                else:
                    os.remove(link)
            elif os.path.isfile(link) or os.path.isdir(link):
                shutil.rmtree(link)
            if create:
                os.makedirs(os.path.dirname(link))
                os.symlink(extraction_path, link)
            if not os.path.islink(link):
                raise RuntimeError('link %s was not created successfuly'
                                   % link)
        return extraction_path

    def copy(self, filename, path, verbose=False):
        if verbose:
            print >> sys.stderr, 'Copying %s (%s)' % (path, filename)
        try:
            self.ensure_dirname(path)
            shutil.copy(filename, path)
        except:
            if os.path.isfile(path):
                os.remove(path)
            raise

    def cache_file_path(self ,cache_dir):
        return os.path.join(cache_dir, self.filename())

    def extraction_path(self, cache_dir):
        filedir = os.path.dirname(self.cache_file_path(cache_dir))
        return os.path.join(filedir, "extracted")

    def download_to_cache(self, cache_dir, verbose):
        filename = self.cache_file_path(cache_dir)
        self.download(filename, verbose)
        return filename

    def assemble(self, cache_dir, project_dir, verbose=False):
        if self.action == "manage":
            self.manage(cache_dir, verbose)
            return

        # check package_id
        path = os.path.join(project_dir, self.dependency.load_value('path'))
        check_package_id = self.dependency.get_bool_value(
            'check_package_id', 'True')
        if check_package_id:
            package_file = os.path.join(path, 'SPOTIFY_PACKAGE_INFO')
            package_id = self.dependency.load_value('package_id')
            if os.path.exists(package_file):
                with open(package_file, 'r') as file:
                    info = file.readline().strip()
                if info == package_id:
                    return
        # download to cache
        filename = self.download_to_cache(cache_dir, verbose)
        # remove dependency
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        # extract or copy dependency
        if self.action == 'extract':
            self.extract(filename, path, verbose)
        elif self.action == 'copy':
            self.copy(filename, path, verbose)
        else:
            raise RuntimeError('invalid action %s:' % self.action)
        # check package_id again
        if check_package_id:
            if not os.path.isfile(package_file):
                raise RuntimeError(
                    'file %s does not contain SPOTIFY_PACKAGE_INFO' % filename)
            with open(package_file, 'r') as file:
                info = file.readline().strip()
            if info != package_id:
                raise RuntimeError(
                    ('SPOTIFY_PACKAGE_INFO does not contain '
                     'proper package_id %s: %s') % (package_id, info))

    def lookup_resource_id(self, cache_dir, project_dir):
        if self.action == "manage":
            return self.extraction_path(cache_dir)

        return os.path.join(project_dir, self.dependency.load_value('path'))

    @staticmethod
    def human_readable_size(size, precision=2):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffixIndex = 0
        while size > 1024 and suffixIndex < 4:
            suffixIndex += 1 #increment the index of the suffix
            size = size/1024.0 #apply the division
        return "%.*f%s"%(precision,size,suffixes[suffixIndex])
