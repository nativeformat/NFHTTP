import os
import sys
import shutil
import tempfile
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import Dependency
from spotify_vulcan.assembler_url import UrlAssembler


class TestDownloadUrlArtifactoryWithoutInfo(unittest.TestCase):

    def test_assemble(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test-without-info.zip')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test',
                      'check_package_id': 'false'}
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
            filename = os.path.join(cache_dir, 'test-without-info.zip-' +
                                    '58871069b6746a29d008a78647e0ef4e1b016a97',
                                    'test-without-info.zip')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'test')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertFalse(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_manage(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test-without-info.zip')
        definition = {'type': 'url', 'url': url,
                      'action': 'manage'}
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

            # Verify download location
            downloaded_dirname = ('test-without-info.zip-' +
                                  '58871069b6746a29d008a78647e0ef4e1b016a97')
            downloaded_name = os.path.join(downloaded_dirname,
                                           'test-without-info.zip')
            downloaded = os.path.join(cache_dir, downloaded_name)
            self.assertTrue(os.path.isfile(downloaded))

            # Verify extraction location
            extracted = os.path.join(cache_dir, downloaded_dirname,
                                     'extracted')
            self.assertTrue(os.path.isdir(extracted))

            # Verify extracted file location
            filename = os.path.join(extracted, 'SPOTIFY_PACKAGE_INFO')
            self.assertFalse(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_manage_with_path(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test-without-info.zip')
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test',
                      'check_package_id': 'false',
                      'action': 'manage'}
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
            self.fail("Expected exception from assemble()")
        except RuntimeError, e:
            self.assertTrue(("manage" in str(e)) and ("path" in str(e)),
                            'Exception should say that "manage"' +
                            ' and "path" are incompatible: <%s>' % e)
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_manage_with_check_package_id(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test-without-info.zip')
        definition = {'type': 'url', 'url': url,
                      'check_package_id': 'false',
                      'action': 'manage'}
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
            self.fail("Expected exception from assemble()")
        except RuntimeError, e:
            self.assertTrue(("manage" in str(e)) and
                            ("check_package_id" in str(e)),
                            'Exception should say that "manage" and' +
                            ' "check_package_id" are incompatible: <%s>' % e)
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_manage_with_package_id(self):
        url = ('https://artifactory.spotify.net/artifactory/'
               'client-infrastructure/test/test-without-info.zip')
        definition = {'type': 'url', 'url': url,
                      'package_id': 'test',
                      'action': 'manage'}
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
            self.fail("Expected exception from assemble()")
        except RuntimeError, e:
            self.assertTrue(("manage" in str(e)) and
                            ("package_id" in str(e)) and
                            ("check_package_id" not in str(e)),
                            'Exception should say that "manage" and ' +
                            '"package_id" are incompatible: <%s>' % e)
        finally:
            shutil.rmtree(dirname, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
