import os
import sys
import shutil
import tempfile
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import Dependency
from spotify_vulcan.assembler_url import UrlAssembler


class TestDownloadUrlArtifactory(unittest.TestCase):

    def test_assemble_zip(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test.zip')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            cache_dir = os.path.join(dirname, 'cache')
            os.mkdir(cache_dir)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            self.downloader.assemble(cache_dir, project_dir)
            filename = os.path.join(cache_dir, 'test.zip-' +
                                    '6a519e52e70ab1521ee6a70c6d77927b101f0a90',
                                    'test.zip')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_assemble_tar(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test.tar')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            cache_dir = os.path.join(dirname, 'cache')
            os.mkdir(cache_dir)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            self.downloader.assemble(cache_dir, project_dir)
            filename = os.path.join(cache_dir, 'test.tar-' +
                                    'c8ea0521bc3b8055b64655451ff5cb1bc3eef3f9',
                                    'test.tar')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_assemble_tar_gz(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test.tar.gz')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            cache_dir = os.path.join(dirname, 'cache')
            os.mkdir(cache_dir)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            self.downloader.assemble(cache_dir, project_dir)
            filename = os.path.join(cache_dir, 'test.tar.gz-' +
                                    'bf418904b62e487a490b327373d6a35dde0f50f5',
                                    'test.tar.gz')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_assemble_tgz(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test.tgz')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            cache_dir = os.path.join(dirname, 'cache')
            os.mkdir(cache_dir)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            self.downloader.assemble(cache_dir, project_dir)
            filename = os.path.join(cache_dir, 'test.tgz-' +
                                    '9a36558db79048c043f118a4e1d5782741e259ba',
                                    'test.tgz')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_assemble_tar_bz2(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test.tar.bz2')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            cache_dir = os.path.join(dirname, 'cache')
            os.mkdir(cache_dir)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            self.downloader.assemble(cache_dir, project_dir)
            filename = os.path.join(cache_dir, 'test.tar.bz2-' +
                                    '73a4ef0add8baf029c5de252b565a136ea88744e',
                                    'test.tar.bz2')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
