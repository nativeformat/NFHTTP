import os
import sys
import random

import shutil
import unittest
import tempfile
import requests

test_folder = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(test_folder)
sys.path.insert(1, root_path)
import spotify_vulcan.cache_manager as cm


class MockRequestsGet(object):
    def __init__(self, status_codes=(200,), response_text=None):
        self.status_codes = status_codes
        self.response_text = response_text
        self.status_ix = 0

    def __call__(self, url, **kwargs):
        r = requests.Response()
        r.status_code = self.status_codes[self.status_ix]
        r._content = self.response_text
        self.status_ix += 1
        return r


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.temp_vulcan_folder = tempfile.mkdtemp()
        self.cache = os.path.join(self.temp_vulcan_folder, 'cache')
        os.mkdir(self.cache)
        self.cm_under_test = cm.CacheManager(vulcan_file=os.path.join(test_folder, "test_vulcan_file.vulcan"), vulcan_folder=self.temp_vulcan_folder, do_logging=False)

    def tearDown(self):
        shutil.rmtree(self.temp_vulcan_folder)

    def _create_mock_artifact(self, artifact_dir_name="some_artifact_dir", artifact_file_name="some_artifact", artifact_size_bytes=100000, artifact_last_accessed=0):
        artifact_path = os.path.join(self.cache, artifact_dir_name)

        if os.path.exists(artifact_path):
            shutil.rmtree(artifact_path)

        os.mkdir(artifact_path)

        with open(os.path.join(artifact_path, artifact_file_name), 'w') as ar:
            ar.write('a'*artifact_size_bytes)

        with open(os.path.join(artifact_path, "metadata.json"), 'w') as meta:
            meta.write('{\n"last-used": %s,\n' % (artifact_last_accessed,))
            meta.write('"content-length": %s\n}' % (artifact_size_bytes,))

    def test_sorting_artifacts_by_last_accessed(self):
        # Arrange
        self._create_mock_artifact(artifact_dir_name="ar1", artifact_last_accessed=2, artifact_size_bytes=10)
        self._create_mock_artifact(artifact_dir_name="ar2", artifact_last_accessed=0, artifact_size_bytes=10)
        self._create_mock_artifact(artifact_dir_name="ar3", artifact_last_accessed=1, artifact_size_bytes=10)

        expected = [os.path.join(self.cache, ar) for ar in ['ar2', 'ar3', 'ar1']]

        # Act
        actual = [ar.artifact_path for ar in self.cm_under_test.get_sorted_artifacts()]

        # Assert
        self.assertEqual(expected, actual)

    def test_sort_uses_size_as_secondary_key(self):
        # Arrange
        self._create_mock_artifact(artifact_dir_name="ar1", artifact_last_accessed=2, artifact_size_bytes=10)
        self._create_mock_artifact(artifact_dir_name="ar2", artifact_last_accessed=0, artifact_size_bytes=10)
        self._create_mock_artifact(artifact_dir_name="ar3", artifact_last_accessed=2, artifact_size_bytes=5)

        expected = [os.path.join(self.cache, ar) for ar in ['ar2', 'ar1', 'ar3']]

        # Act
        actual = [ar.artifact_path for ar in self.cm_under_test.get_sorted_artifacts()]

        # Assert
        self.assertEqual(expected, actual)

    def test_atomic_delete(self):
        # Arrange
        artifact_dir = "some_artifact_dir.delete"
        self._create_mock_artifact(artifact_dir_name=artifact_dir, artifact_file_name="an_artifact")

        # Act
        self.cm_under_test.delete_remains()

        # Assert
        self.assertFalse(os.path.exists(os.path.join(self.cache, artifact_dir)), self.cache)

    def test_sorts_correctly_if_json_is_missing(self):
        # Arrange
        # ar1 will be created before/at the same time as ar3 and is slightly larger, so it will be deleted first.
        self._create_mock_artifact(artifact_dir_name="ar1", artifact_last_accessed=2, artifact_size_bytes=15)
        self._create_mock_artifact(artifact_dir_name="ar2", artifact_last_accessed=0, artifact_size_bytes=10)
        self._create_mock_artifact(artifact_dir_name="ar3", artifact_last_accessed=1, artifact_size_bytes=10)

        os.remove(os.path.join(self.cache, 'ar1', 'metadata.json'))
        os.remove(os.path.join(self.cache, 'ar3', 'metadata.json'))

        expected = [os.path.join(self.cache, ar) for ar in ['ar2', 'ar1', 'ar3']]


        # Act
        actual = [ar.artifact_path for ar in self.cm_under_test.get_sorted_artifacts()]

        # Assert
        self.assertEqual(expected, actual)

    def test_deletes_from_least_used_artifacts_just_enough_to_reach_target_free_space(self):
        # Arrange
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted1", artifact_last_accessed=0)
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted2", artifact_last_accessed=1)
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_remain", artifact_last_accessed=2)

        # Act
        self.cm_under_test._free_space(target_free_space=(cm.CacheManager.disk_usage(self.cache).free + 150000))

        # Assert
        self.assertTrue(os.path.exists(os.path.join(self.cache, "this_artifact_will_remain")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted1")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted2")))

    def test_never_deletes_essential_build_artifacts(self):
        # Arrange
        self._create_mock_artifact(artifact_dir_name="this_artifact_is_essential_and_will_remain", artifact_last_accessed=0) # Highest priority to delete from last-accessed perspective
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted1", artifact_last_accessed=1)
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted2", artifact_last_accessed=2)
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_remain", artifact_last_accessed=3)

        self.cm_under_test.artifacts_dirs.append(os.path.join(self.cache, "this_artifact_is_essential_and_will_remain"))

        # Act
        self.cm_under_test._free_space(target_free_space=(cm.CacheManager.disk_usage(self.cache).free + 150000))

        # Assert
        self.assertTrue(os.path.exists(os.path.join(self.cache, "this_artifact_is_essential_and_will_remain")))
        self.assertTrue(os.path.exists(os.path.join(self.cache, "this_artifact_will_remain")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted1")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted2")))


    def test_raises_exception_if_impossible_to_clear_enough_space(self):
        # Arrange
        self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted1", artifact_last_accessed=0)

        # Act + Assert
        with self.assertRaises(cm.CacheManager.CannotFreeSpaceError) as e:
            self.cm_under_test._free_space(target_free_space=(cm.CacheManager.disk_usage(self.cache).free + 150000))

        # Assert
        self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted1")))

    def test_get_bytes_from_size_string(self):

        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("0k"), 0)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("1m"), 1048576)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("1g"), 1073741824)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("200"), 200)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("100K"), 102400)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("200M"), 209715200)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("20g"), 21474836480)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("2000G"), 2147483648000)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("2000  G"), 2147483648000)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("  2000G "), 2147483648000)
        self.assertEquals(self.cm_under_test.get_bytes_from_size_string("20t"), 21990232555520)

    def test_defaults(self):

       self.cm_under_test = cm.CacheManager(vulcan_file=os.path.join(test_folder, "test_vulcan_file2.vulcan"), vulcan_folder=self.temp_vulcan_folder, do_logging=False)

        # Arrange
       self._create_mock_artifact(artifact_dir_name="this_artifact_is_essential_and_will_remain", artifact_last_accessed=0) # Highest priority to delete from last-accessed perspective
       self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted1", artifact_last_accessed=1)
       self._create_mock_artifact(artifact_dir_name="this_artifact_will_be_deleted2", artifact_last_accessed=2)
       self._create_mock_artifact(artifact_dir_name="this_artifact_will_remain", artifact_last_accessed=3)

       self.cm_under_test.artifacts_dirs.append(os.path.join(self.cache, "this_artifact_is_essential_and_will_remain"))

        # Act
       self.cm_under_test._free_space(target_free_space=(cm.CacheManager.disk_usage(self.cache).free + 150000))

        # Assert
       self.assertTrue(os.path.exists(os.path.join(self.cache, "this_artifact_is_essential_and_will_remain")))
       self.assertTrue(os.path.exists(os.path.join(self.cache, "this_artifact_will_remain")))
       self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted1")))
       self.assertFalse(os.path.exists(os.path.join(self.cache, "this_artifact_will_be_deleted2")))

    def test_creates_cache_dir(self):

       testfolder = os.path.join(self.temp_vulcan_folder, str(random.randint(1, 99999999)))
       self.assertFalse(os.path.exists(testfolder))
       self.cm_under_test = cm.CacheManager(vulcan_file=os.path.join(test_folder, "test_vulcan_file2.vulcan"), vulcan_folder=testfolder, do_logging=False)
       self.assertTrue(os.path.exists(testfolder))

    def test_http_get_with_retry_fail(self):
        requests_get_mock = MockRequestsGet(status_codes=(504, 504,))
        with self.assertRaises(requests.exceptions.HTTPError):
            response = self.cm_under_test.http_get(
                'http://fakeurl.example.com', auth=None, max_retries=1,
                retry_for_status_codes=(504,), backoff_factor=0.01,
                get_method=requests_get_mock)

    def test_http_get_with_retry_success(self):
        requests_get_mock = MockRequestsGet(status_codes=(504, 200,),
                                            response_text='Wee!')
        response = self.cm_under_test.http_get(
            'http://fakeurl.example.com', auth=None, max_retries=1,
            retry_for_status_codes=(504,), backoff_factor=0.01,
            get_method=requests_get_mock)
        self.assertEqual(response.text, 'Wee!')


class TeamCityFormatterTest(unittest.TestCase):
    def test_formatting(self):
        tricky_string = u"'|\n\r][\u0085\u2028\u2029"
        formatter = cm.TeamCityFormatter()
        escaped_string = formatter.tc_msg_escape(tricky_string)
        self.assertEquals(escaped_string, "|'|||n|r|]|[|x|l|p")


if __name__ == '__main__':
    unittest.main()
