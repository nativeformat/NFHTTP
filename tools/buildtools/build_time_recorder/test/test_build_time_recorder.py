# -*- coding: utf-8 -*-
# Copyright (c) 2015 Spotify AB

import os
import os.path
import mock
import json
import argparse
import tempfile
import unittest
import subprocess
import sys

import build_time_recorder as btr


class BuildTimeRecorderTest(unittest.TestCase):
    def setUp(self):
        def mock_check_output(*args, **kwargs):
            canned_responses = {
                'git describe --long':
                    'latest_tag-distance_from_here-short_sha',
                'hostname': 'some_hostname'}
            args = " ".join(args[0])
            return canned_responses.get(args)

        # So we can mock the options
        class FakeOptions(object):
            timefile = None
            file = None
            json = None
            dry = None
            version = 1
        self.mock_options = FakeOptions()

        #  Get a temporary filename for tempfile options
        tf = tempfile.NamedTemporaryFile(delete=True)
        self.timefile_name = tf.name
        tf.close()
        self.mock_options.timefile = self.timefile_name

        # Mock httplib so we never make requests during tests
        self.mock_httplib = mock.Mock()
        btr.httplib = self.mock_httplib
        self.mock_conn = self.mock_httplib.HTTPConnection.return_value
        self.mock_response = mock.Mock()
        self.mock_conn.getresponse.return_value = self.mock_response

        # Mock get_facter_info to return constant json output
        btr.get_facter_info = mock.Mock()
        btr.get_facter_info.return_value = {'memorysize_mb': '1234.5'}

        # Mock get_environment_identifier to return constant id
        self.real_get_environment_identifier = btr.get_environment_identifier
        btr.get_environment_identifier = mock.Mock()
        btr.get_environment_identifier.return_value = '2eb66f9e9b244937a33d0180d857a944'  # NOQA

        btr.log = mock.Mock()

        btr.log.exception = mock.Mock(side_effect=self._capture_exception)
        self._exception_expected = False
        self._exception = None

        btr.subprocess.check_output = mock.Mock()
        btr.subprocess.check_output.side_effect = mock_check_output

        # Create expected dict for "example_with_duration.json"
        self.expected_json = self._load_json_test_file(
            "example_with_duration.json")
        self.expected_json['system'] = {'mem_total_mb': 1234.5}
        self.expected_json['git_describe'] = \
            "latest_tag-distance_from_here-short_sha"
        self.expected_json['is_ci_agent'] = True
        self.expected_json['@timestamp'] = 777000
        self.expected_json['ci_agent_hostname'] = 'some_hostname'

    def _capture_exception(self, message):
        (e_type, e_value, e_traceback) = sys.exc_info()
        if not self._exception_expected:
            print "Unexpected Exception:  type={}, value={}, tb={}".format(
                e_type, e_value, e_traceback)
        self._exception_message = message
        self._exception = e_value

    def _create_timefile(self, content="666"):
        timefile = tempfile.NamedTemporaryFile(delete=True)
        self.mock_options.timefile = timefile.name
        timefile.close()

        with open(self.mock_options.timefile, 'w') as tf:
            tf.write(content)

    def tearDown(self):
        btr.get_environment_identifier = self.real_get_environment_identifier
        if os.path.exists(self.timefile_name):
            os.unlink(self.timefile_name)
        id_file_path = os.path.join(
                os.path.expanduser("~"), btr.ENV_ID_FILE_NAME)
        if os.path.isfile(id_file_path):
            os.remove(id_file_path)

    def test_start_creates_timefile_with_time_since_epoch(self):
        #  Arrange

        #  fake time since epoch
        mock_time = mock.Mock()
        btr.BuildTimeRecorder._time_since_epoch_ms = mock_time
        mock_time.return_value = 777000

        #  Act
        btr.BuildTimeRecorder.start(self.mock_options)

        #  Assert
        self.assertTrue(os.path.exists(self.mock_options.timefile))
        with open(self.timefile_name, 'r') as timefile:
            self.assertEqual("777000", timefile.read())

    def test_stop_must_recieve_timefile_in_options(self):
        #  Arrange
        empty_options = argparse.Namespace()

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(empty_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_timefile_must_exist(self):
        #  Arrange
        tf = tempfile.NamedTemporaryFile(delete=True)
        non_existing_file = tf.name
        tf.close()

        self.mock_options.timefile = non_existing_file

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_timefile_must_contain_valid_unit_timestamp_not_a_number(
            self):
        #  Arrange
        self._create_timefile("This is not a valid unix timestamp")

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_timefile_must_contain_valid_unit_timestamp_negative_number(
            self):
        #  Arrange
        self._create_timefile("-220")

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_must_set_file_or_json_option(self):
        #  Arrange
        self._create_timefile("200")

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_file_passed_in_option_exist(self):
        #  Arrange
        self._create_timefile("200")
        self.mock_options.file = "/sdfhyrdkuk/ThisFileDoesNotExist"

        #  Act
        with self.assertRaises(SystemExit):
            btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong during stop()..")

    def test_stop_dryrun_with_file_just_prints_data(self):
        #  Arrange
        self._create_timefile("200")
        self.mock_options.dry = True
        self.mock_options.file = os.path.join(
            os.path.dirname(__file__),
            "example_with_duration.json")

        expected = json.dumps(
            self.expected_json,
            sort_keys=True, indent=4, separators=(',', ': '))

        #  Act
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.info.assert_called_once_with(
            expected)

    def _load_json_test_file(self, filename):
        json_file = os.path.join(
            os.path.dirname(__file__),
            filename)

        with open(json_file, 'r') as example_json:
            return json.load(example_json)

    def test_get_git_describe_happy_path(self):
        # Arrange
        d = dict()

        # Act
        btr.BuildTimeRecorder.populate_date_with_git_describe(d)

        # Assert
        self.assertEqual(
            "latest_tag-distance_from_here-short_sha",
            d['git_describe'])

    def test_get_git_describe_fails_with_process_error(self):
        # Arrange
        d = dict()
        returncode = 'error_return_code'
        stderr = 'stderr_output'
        btr.subprocess.check_output.side_effect = \
            subprocess.CalledProcessError(
                cmd='git describe --long',
                returncode=returncode,
                output=stderr)

        # Act
        btr.BuildTimeRecorder.populate_date_with_git_describe(d)

        # Assert
        self.assertEqual(
            "'git describe --long' (fails if there are no tags with "
            "'No names found..') returned {}: {}".format(returncode, stderr),
            d['git_describe'])

    def test_get_git_describe_fails_with_unexpected_exception(self):
        # Arrange
        d = dict()
        btr.subprocess.check_output.side_effect = Exception("Boom!")

        # Act
        btr.BuildTimeRecorder.populate_date_with_git_describe(d)

        # Assert
        btr.log.exception.assert_called_once_with(
            "Something went wrong with 'git describe --long'..")

    def test_stop_dryrun_with_json_just_prints_data(self):
        #  Arrange
        self._create_timefile("200")
        self.mock_options.dry = True

        expected = json.dumps(
            self.expected_json,
            sort_keys=True, indent=4, separators=(',', ': '))

        self.mock_options.json = expected

        #  Act
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        btr.log.info.assert_called_once_with(
            expected)

    def test_stop_deletes_timefile(self):
        #  Arrange
        self.mock_post_to_index = mock.Mock(
            spec=btr.BuildTimeRecorder.post_to_index)
        btr.BuildTimeRecorder.post_to_index = \
            self.mock_post_to_index

        self._create_timefile("200")
        self.mock_options.dry = False
        self.mock_options.file = os.path.join(
            os.path.dirname(__file__),
            "example_without_duration.json")

        #  Act
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        self.assertFalse(os.path.exists(self.mock_options.timefile))

    def test_stop_calculates_duration_since_start_and_posts_to_index(self):
        #  Arrange

        self.mock_post_to_index = mock.Mock(
            spec=btr.BuildTimeRecorder.post_to_index)
        btr.BuildTimeRecorder.post_to_index = self.mock_post_to_index

        self._create_timefile("200000")
        self.mock_options.dry = False
        self.mock_options.file = os.path.join(
            os.path.dirname(__file__),
            "example_without_duration.json")

        '''
        We expect duration_ms to be 577 because
        we create a timefile with 200 in 'Arrange' and we're mocking
        _time_since_epoch_ms() in setUp() to return 777000 and
        777s - 200s = 577s :)
        '''
        self.expected_json['duration_ms'] = 577000

        #  Act
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert

        self.mock_post_to_index.assert_called_once_with(
            self.expected_json, version=1)

    def test_post_to_index_posts_payload_to_data(self):
        # Arrange
        fake_endpoint = object()
        fake_payload = {"fake": "payload"}
        self.mock_response.status = 200

        # Act
        btr.BuildTimeRecorder.post_to_index(
            fake_payload, fake_endpoint)

        # Assert
        self.mock_httplib.HTTPConnection.assert_called_once_with(fake_endpoint)
        self.mock_conn.request.assert_called_once_with(
            "POST", '/api/v1/btr/record', json.dumps(fake_payload))

    def test_post_to_index_posts_payload_to_v2_endpoint(self):
        # Arrange
        fake_endpoint = object()
        fake_payload = {"fake": "payload"}
        self.mock_response.status = 200

        # Act
        btr.BuildTimeRecorder.post_to_index(
            fake_payload, fake_endpoint, version=2)

        # Assert
        self.mock_httplib.HTTPConnection.assert_called_once_with(fake_endpoint)
        self.mock_conn.request.assert_called_once_with(
            "POST", '/api/v2/btr/record', json.dumps(fake_payload))

    def test_post_to_index_raises_an_exception_on_fail_status_code(self):
        # Arrange
        fake_endpoint = "fake_endpoint"
        fake_payload = {"fake": "payload"}
        self.mock_response.status = 500
        self.mock_response.read.return_value = "ERROR!!"

        # Act
        with self.assertRaises(Exception):
            btr.BuildTimeRecorder.post_to_index(
                fake_payload, fake_endpoint)

    def test_stop_posts_environment_id(self):
        #  Arrange
        btr.get_environment_identifier.return_value = '5179a73add8a4cc8ac66a904e017b5a0'
        self.mock_post_to_index = mock.Mock(
                spec=btr.BuildTimeRecorder.post_to_index)
        btr.BuildTimeRecorder.post_to_index = self.mock_post_to_index

        self._create_timefile("200")
        self.mock_options.dry = False
        self.mock_options.file = os.path.join(
                os.path.dirname(__file__),
                "example_without_identifier.json")
        self.expected_json['environment_id'] = '5179a73add8a4cc8ac66a904e017b5a0'

        #  Act
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        self.mock_post_to_index.assert_called_once_with(
                self.expected_json, version=1)

    def test_stop_writes_v2_timestamp(self):
        #  Arrange
        self.mock_post_to_index = mock.Mock(
                spec=btr.BuildTimeRecorder.post_to_index)
        btr.BuildTimeRecorder.post_to_index = self.mock_post_to_index

        self._create_timefile("200")
        self.mock_options.dry = False
        self.mock_options.file = os.path.join(
                os.path.dirname(__file__),
                "example_without_identifier.json")
        timestamp_ms = self.expected_json.pop('@timestamp')
        self.expected_json['timestamp'] = timestamp_ms / 1000
        self.expected_json['machine_id'] = self.expected_json.pop(
                'environment_id')

        #  Act
        self.mock_options.version = 2
        btr.BuildTimeRecorder.stop(self.mock_options)

        #  Assert
        self.mock_post_to_index.assert_called_once_with(
                self.expected_json, version=2)

    def test_stop_creates_id_file(self):
        #  Arrange
        btr.get_environment_identifier = self.real_get_environment_identifier

        #  Act
        generated_id = btr.get_environment_identifier()

        #  Assert
        self.assertEquals(btr.ENV_ID_LENGTH, len(generated_id))
        id_file_path = os.path.join(os.path.expanduser("~"), btr.ENV_ID_FILE_NAME)
        self.assertTrue(os.path.isfile(id_file_path))
        with open(id_file_path, 'r') as id_file:
            self.assertEqual(generated_id, id_file.read())

    def test_stop_does_not_recreates_id_file(self):
        #  Arrange
        btr.get_environment_identifier = self.real_get_environment_identifier

        #  Act
        generated_id = btr.get_environment_identifier()
        second_call_id = btr.get_environment_identifier()

        #  Assert
        self.assertEquals(btr.ENV_ID_LENGTH, len(generated_id))
        self.assertEquals(second_call_id, generated_id)

    def test_processor_ghz_parsing(self):
        self.assertEqual(btr.parse_processor_ghz('3.13GHz'), 3.13)
        self.assertEqual(btr.parse_processor_ghz('2.2 GHz'), 2.2)
        self.assertEqual(btr.parse_processor_ghz('1 ghz'), 1)
        self.assertEqual(btr.parse_processor_ghz('.25GHZ'), 0.25)
        self.assertEqual(btr.parse_processor_ghz('1.01'), None)
        self.assertEqual(btr.parse_processor_ghz(''), None)
        self.assertEqual(btr.parse_processor_ghz(None), None)
        self.assertEqual(btr.parse_processor_ghz(object()), None)

    def test_safe_float(self):
        # simple tests as this just wraps float()
        self.assertEqual(btr.safe_float('1.01'), 1.01)
        self.assertEqual(btr.safe_float('.25'), 0.25)
        self.assertEqual(btr.safe_float('8'), 8)
        self.assertEqual(btr.safe_float('foo'), None)
        self.assertEqual(btr.safe_float(object()), None)

    def test_safe_int(self):
        # simple tests as this just wraps int()
        self.assertEqual(btr.safe_float('8'), 8)
        self.assertEqual(btr.safe_float('8x'), None)
        self.assertEqual(btr.safe_float('foo'), None)
        self.assertEqual(btr.safe_float(object()), None)

    def test_parse_bool(self):
        self.assertEqual(btr.parse_bool('true'), True)
        self.assertEqual(btr.parse_bool('TRUE'), True)
        self.assertEqual(btr.parse_bool('t'), True)
        self.assertEqual(btr.parse_bool('yes'), True)
        self.assertEqual(btr.parse_bool('Y'), True)
        self.assertEqual(btr.parse_bool('1'), True)
        self.assertEqual(btr.parse_bool(1), True)
        self.assertEqual(btr.parse_bool(True), True)
        self.assertEqual(btr.parse_bool('false'), False)
        self.assertEqual(btr.parse_bool('FALSE'), False)
        self.assertEqual(btr.parse_bool('f'), False)
        self.assertEqual(btr.parse_bool('no'), False)
        self.assertEqual(btr.parse_bool('N'), False)
        self.assertEqual(btr.parse_bool('0'), False)
        self.assertEqual(btr.parse_bool(0), False)
        self.assertEqual(btr.parse_bool(False), False)
        self.assertEqual(btr.parse_bool(None), None)
        self.assertEqual(btr.parse_bool(33), None)
        self.assertEqual(btr.parse_bool('foo'), None)
        self.assertEqual(btr.parse_bool(object()), None)

    def test_recursive_get(self):
        d = {'foo': {'bar': ['a', 'b', 'c']}, 'hello': 'world'}
        self.assertEqual(btr.recursive_get(d, ['hello']), 'world')
        self.assertEqual(
            btr.recursive_get(d, ['foo']),
            {'bar': ['a', 'b', 'c']})
        obj = object()

        self.assertEqual(btr.recursive_get(d, ['foo', 'bar']), ['a', 'b', 'c'])
        self.assertEqual(btr.recursive_get(d, ['foo', 'bar', 0]), 'a')
        self.assertEqual(btr.recursive_get(d, ['foo', 'bar', 1]), 'b')
        self.assertEqual(btr.recursive_get(d, ['foo', 'bar', 2]), 'c')
        self.assertEqual(btr.recursive_get(d, ['foo', 'bar', 3]), None)
        self.assertEqual(btr.recursive_get(obj, 'a'), None)
        self.assertEqual(btr.recursive_get(d, 'blah'), None)
        self.assertEqual(btr.recursive_get(d, None), d)
        self.assertEqual(btr.recursive_get(obj, None), obj)

    def test_system_info_cpu_model(self):
        facter = {
            'processors': {'models': ['abc', 'def']},
            'processor0': 'blah',
            'sp_cpu_type': 'foo'
        }
        btr.get_facter_info.return_value = facter

        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_model'), 'abc')

        del facter['processors']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_model'), 'blah')

        del facter['processor0']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_model'), 'foo')

    def test_system_info_cpu_count(self):
        facter = {
            'sp_number_processors': '5',
            'processors': {'count': '8'},
            'processorcount': '3'
        }
        btr.get_facter_info.return_value = facter

        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_count'), 5)

        del facter['sp_number_processors']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_count'), 8)

        del facter['processors']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_count'), 3)

    def test_system_info_cpu_speed_ghz(self):
        facter = {
            'sp_current_processor_speed': 'blah blah 3.2GHZ',
            'processors': {'speed': '1.2 GHz', 'models': ['blah @ 2.0ghz']}
        }
        btr.get_facter_info.return_value = facter

        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_speed_ghz'), 3.2)

        del facter['sp_current_processor_speed']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_speed_ghz'), 1.2)

        del facter['processors']['speed']
        info = btr.get_system_info()
        self.assertEqual(info.get('cpu_speed_ghz'), 2.0)

    def test_system_host_arch(self):
        btr.get_facter_info.return_value = {'hardwareisa': 'foo'}
        info = btr.get_system_info()
        self.assertEqual(info.get('host_arch'), 'foo')

    def test_system_host_model(self):
        btr.get_facter_info.return_value = {'productname': 'foo'}
        info = btr.get_system_info()
        self.assertEqual(info.get('host_model'), 'foo')

    def test_system_host_os_family(self):
        btr.get_facter_info.return_value = {'osfamily': 'foo'}
        info = btr.get_system_info()
        self.assertEqual(info.get('host_os_family'), 'foo')

    def test_system_host_os(self):
        facter = {
            'macosx_productname': 'foo',
            'operatingsystem': 'bar'
        }
        btr.get_facter_info.return_value = facter

        info = btr.get_system_info()
        self.assertEqual(info.get('host_os'), 'foo')

        del facter['macosx_productname']
        info = btr.get_system_info()
        self.assertEqual(info.get('host_os'), 'bar')

    def test_system_host_os_version(self):
        facter = {
            'macosx_productversion': 'foo',
            'operatingsystemrelease': 'bar'
        }
        btr.get_facter_info.return_value = facter

        info = btr.get_system_info()
        self.assertEqual(info.get('host_os_version'), 'foo')

        del facter['macosx_productversion']
        info = btr.get_system_info()
        self.assertEqual(info.get('host_os_version'), 'bar')

    def test_system_is_virtual(self):
        btr.get_facter_info.return_value = {'is_virtual': 'true'}
        info = btr.get_system_info()
        self.assertEqual(info.get('is_virtual'), True)

    def test_system_mem_total_mb(self):
        btr.get_facter_info.return_value = {'memorysize_mb': '123.4'}
        info = btr.get_system_info()
        self.assertEqual(info.get('mem_total_mb'), 123.4)

    def test_system_mem_free_mb(self):
        btr.get_facter_info.return_value = {'memoryfree_mb': '123.4'}
        info = btr.get_system_info()
        self.assertEqual(info.get('mem_free_mb'), 123.4)

    def test_system_swap_total_mb(self):
        btr.get_facter_info.return_value = {'swapsize_mb': '123.4'}
        info = btr.get_system_info()
        self.assertEqual(info.get('swap_total_mb'), 123.4)

    def test_system_swap_free_mb(self):
        btr.get_facter_info.return_value = {'swapfree_mb': '123.4'}
        info = btr.get_system_info()
        self.assertEqual(info.get('swap_free_mb'), 123.4)

    def test_system_uptime_s(self):
        btr.get_facter_info.return_value = {'uptime_seconds': '123'}
        info = btr.get_system_info()
        self.assertEqual(info.get('uptime_s'), 123)

    def test_system_timezone(self):
        btr.get_facter_info.return_value = {'timezone': 'EST'}
        info = btr.get_system_info()
        self.assertEqual(info.get('timezone'), 'EST')
