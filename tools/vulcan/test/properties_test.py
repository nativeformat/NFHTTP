import unittest
import os
import sys

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.properties import parse_properties


class TestProperties(unittest.TestCase):

    def test_parse_properties_empty(self):
        self.assertEqual({}, parse_properties())

    def test_parse_properties_without_equals(self):
        self.assertEqual({'foo': ''}, parse_properties('foo'))

    def test_parse_properties_without_value(self):
        self.assertEqual({'foo': ''}, parse_properties('foo='))

    def test_parse_properties_with_value(self):
        self.assertEqual({'foo': 'bar'}, parse_properties('foo=bar'))

    def test_parse_properties_multiple(self):
        self.assertEqual({'foo': 'bar', 'baz': '', 'qux': ''},
                         parse_properties('foo=bar', 'baz', 'qux='))


if __name__ == '__main__':
    unittest.main()
