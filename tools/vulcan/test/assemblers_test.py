import os
import sys
import shutil
import tempfile
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.assemblers import assemble_project


class TestAssemblers(unittest.TestCase):

    def test_assemble_project(self):
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
            filename = os.path.join(vulcan_folder, 'cache', 'guice-3.0.zip-' +
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

if __name__ == '__main__':
    unittest.main()
