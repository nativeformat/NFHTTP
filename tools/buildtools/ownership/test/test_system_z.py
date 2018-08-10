import vcr
import unittest
import os
import mock

import system_z


def local_cassette(name):
    my_dir = os.path.dirname(__file__)
    filename = '{}.yml'.format(name)
    path = os.path.join(my_dir, 'fixtures', 'cassettes', filename)
    return vcr.use_cassette(path)


class SystemZTest(unittest.TestCase):

    @local_cassette('system_z_valid')
    def test_post_and_delete(self):
        system_z.util = mock.MagicMock()

        out = system_z.synchronize_system_z('fakeorg/fakerepo')

        expected_posted = set([
            'ghe:/fakeorg/fakerepo/baz/service-info.yaml',
            'ghe:/fakeorg/fakerepo/foo/service-info.yaml',
            'ghe:/fakeorg/fakerepo/service-info.yaml'
        ])

        expected_deleted = set([
            'ghe:/fakeorg/fakerepo/derp/service-info.yaml',
            'ghe:/fakeorg/fakerepo/herp/service-info.yaml'
        ])

        self.assertEqual(out['posted'], expected_posted)
        self.assertEqual(out['deleted'], expected_deleted)
