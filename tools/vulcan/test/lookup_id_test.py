import os
import sys
import shutil
import tempfile
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.assemblers import assemble_project
from spotify_vulcan.assemblers import lookup_resource_id


class TestLookupResourceId(unittest.TestCase):

    def test_resource_lookup(self):
        url = 'https://google-guice.googlecode.com/files/guice-3.0.zip'
        definition = {'id': 'guice', 'type': 'url', 'url': url,
                      'path': 'test_dep', 'package_id': 'test',
                      'check_package_id': 'false'}

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            vulcan_folder = os.path.join(dirname, 'vulcan')
            os.mkdir(vulcan_folder)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            project = {'dependencies': [definition]}
            properties = {'current_os': 'foo'}
            assemble_project(vulcan_folder, project_dir, project, properties)
            path = lookup_resource_id('guice', vulcan_folder, project_dir, project, properties)
            self.assertEqual(path, os.path.join(dirname, "project", "test_dep"))

        finally:
            shutil.rmtree(dirname, ignore_errors=True)

    def test_managed_resource_lookup(self):
        url = 'https://google-guice.googlecode.com/files/guice-3.0.zip'
        definition = {'id': 'guice', 'type': 'url', 'url': url,
                      'action': 'manage'}

        if not 'RUN_INTEGRATION_TESTS' in os.environ:
            raise self.skipTest('integration test')
        dirname = tempfile.mkdtemp()
        try:
            vulcan_folder = os.path.join(dirname, 'vulcan')
            os.mkdir(vulcan_folder)
            project_dir = os.path.join(dirname, 'project')
            os.mkdir(project_dir)
            project = {'dependencies': [definition]}
            properties = {'current_os': 'foo'}
            assemble_project(vulcan_folder, project_dir, project, properties)
            path = lookup_resource_id('guice', vulcan_folder, project_dir, project, properties)
            self.assertEqual(path, os.path.join(vulcan_folder, "cache", 'guice-3.0.zip-' +
                                                'dd124c28f193cef48fdc15648000d7a31c940cc3',
                                                "extracted"))

        finally:
            shutil.rmtree(dirname, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
