import os
import sys
import shutil
import tempfile
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import Dependency
from spotify_vulcan.assembler_url import UrlAssembler


class TestDownloadExternalUrl(unittest.TestCase):

    def test_extract(self):
        url = 'https://google-guice.googlecode.com/files/guice-3.0.zip'
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
            filename = os.path.join(cache_dir, 'guice-3.0.zip-' +
                                    'dd124c28f193cef48fdc15648000d7a31c940cc3',
                                    'guice-3.0.zip')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep', 'guice-3.0',
                                    'guice-3.0.jar')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep', 'guice-3.0',
                                    'SPOTIFY_PACKAGE_INFO')
            self.assertFalse(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_copy_file(self):
        url = 'https://google-guice.googlecode.com/files/guice-3.0.zip'
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test',
                      'action': 'copy', 'check_package_id': 'false'}
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
            filename = os.path.join(cache_dir, 'guice-3.0.zip-' +
                                    'dd124c28f193cef48fdc15648000d7a31c940cc3',
                                    'guice-3.0.zip')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_copy_folder(self):
        url = 'https://google-guice.googlecode.com/files/guice-3.0.zip'
        definition = {'type': 'url', 'url': url,
                      'path': 'test_dep/', 'package_id': 'test',
                      'action': 'copy', 'check_package_id': 'false'}
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
            filename = os.path.join(cache_dir, 'guice-3.0.zip-' +
                                    'dd124c28f193cef48fdc15648000d7a31c940cc3',
                                    'guice-3.0.zip')
            self.assertTrue(os.path.isfile(filename))
            filename = os.path.join(project_dir, 'test_dep')
            self.assertTrue(os.path.isdir(filename))
            filename = os.path.join(project_dir, 'test_dep', 'guice-3.0.zip')
            self.assertTrue(os.path.isfile(filename))
        finally:
            shutil.rmtree(dirname, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
