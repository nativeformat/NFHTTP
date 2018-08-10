import os
import sys
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import Dependency
from spotify_vulcan.dependencies import read_definitions_array
from spotify_vulcan.dependencies import select_dependencies


class TestDependencies(unittest.TestCase):

    def setUp(self):
        self.constant_values = {'current_os': 'linux'}

    def test_read_definitions(self):
        array = [{'foo': 'bar', '~': [{'id': '1'}, {'id': '2', 'foo': 'baz'}]}]
        definitions = read_definitions_array(array)
        self.assertEqual(definitions, [{
                         'id': '1', 'foo': 'bar'}, {'id': '2', 'foo': 'baz'}])

    def test_get_value(self):
        definition = {'foo': 'foo-${bar}', 'bar': 'bar-${baz}', 'baz': 'qux'}
        dependency = Dependency(definition, {})
        foo = dependency.get_value('foo')
        self.assertEqual(foo, 'foo-bar-qux')

    def test_load_value(self):
        definition = {'foo': 'foo-${bar}', 'bar': 'bar-${baz}', 'baz': 'qux'}
        dependency = Dependency(definition, {})
        foo = dependency.load_value('foo')
        self.assertEqual(foo, 'foo-bar-qux')

    def test_get_value_direct_unknown(self):
        definition = {'foo': 'foo-${bar}'}
        dependency = Dependency(definition, {})
        self.assertTrue(dependency.get_value('bar') is None)

    def test_load_value_direct_unknown(self):
        definition = {'foo': 'foo-${bar}'}
        dependency = Dependency(definition, {})
        self.assertRaises(KeyError, dependency.load_value, 'bar')

    def test_get_value_indirect_unknown(self):
        definition = {'foo': 'foo-${bar}'}
        dependency = Dependency(definition, {})
        self.assertRaises(RuntimeError, dependency.get_value, 'foo')

    def test_load_value_indirect_unknown(self):
        definition = {'foo': 'foo-${bar}'}
        dependency = Dependency(definition, {})
        self.assertRaises(RuntimeError, dependency.load_value, 'foo')

    def test_get_values(self):
        definition = {'foo': 'foo-${bar}', 'bar': 'bar-${baz}', 'baz': 'qux'}
        dependency = Dependency(definition, {})
        values = dependency.get_values()
        self.assertEqual(values, {
                         'foo': 'foo-bar-qux', 'bar': 'bar-qux', 'baz': 'qux'})

    def test_get_values_with_circular_depenencies(self):
        definition = {
            'foo': 'foo-${bar}', 'bar': 'bar-${baz}', 'baz': '${foo}'}
        dependency = Dependency(definition, {})
        self.assertRaises(RuntimeError, dependency.get_values)

    def test_select_dependencies_id(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar', 'baz': 'qux'}, {
                         'id': '1', 'os': None, 'current_os': 'linux'}), set())})

    def test_select_dependencies_id_id(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux'})
        select_dependencies(self.constant_values, {}, selected, {'id': '1', 'foo': 'bar2'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar2', 'baz': 'qux'}, {
                         'id': '1', 'os': None, 'current_os': 'linux'}), set())})

    def test_select_dependencies_same_os(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux', 'os': 'linux'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar', 'baz': 'qux', 'os': 'linux'}, {
                         'id': '1', 'os': 'linux', 'current_os': 'linux'}), set(['os']))})

    def test_select_dependencies_diff_os(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux', 'os': 'other'})
        self.assertEqual(selected, {})

    def test_select_dependencies_id_os(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux'})
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar2', 'os': 'linux'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar2', 'os': 'linux'}, {
                         'id': '1', 'os': 'linux', 'current_os': 'linux'}), set(['os']))})

    def test_select_dependencies_os_id(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar2', 'os': 'linux'})
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar2', 'os': 'linux'}, {
                         'id': '1', 'os': 'linux', 'current_os': 'linux'}), set(['os']))})

    def test_select_dependencies_ignore(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux', 'ignore': 'TrUe'})
        self.assertEqual(selected, {})

    def test_select_dependencies_force(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar2', 'os': 'linux'})
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux', 'force': 'TrUe'})
        self.assertEqual(selected, {'1': (Dependency({'id': '1', 'foo': 'bar', 'baz': 'qux', 'force': 'TrUe'}, {
                         'id': '1', 'os': None, 'current_os': 'linux'}), set())})

    def test_select_dependencies_force_more_than_one(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar2', 'os': 'linux'})
        select_dependencies(self.constant_values, {}, selected, {
                            'id': '1', 'foo': 'bar', 'baz': 'qux', 'force': 'TrUe'})
        self.assertRaises(RuntimeError, select_dependencies,
                          self.constant_values, {}, selected, {
                          'id': '1', 'foo': 'bar', 'baz': 'qux', 'force': 'TrUe'})

    def test_select_dependencies_current_os(self):
        selected = {}
        select_dependencies(self.constant_values, {}, selected, {'id': '${current_os}', 'current_os': 'osx'})
        self.assertEqual(selected, {'linux': (Dependency({'id': '${current_os}', 'current_os': 'osx'}, {
                         'id': 'linux', 'os': None, 'current_os': 'linux'}), set())})

    def test_select_dependencies_with_no_filter(self):
        ''' Expect all results '''
        selected = {}
        defs = [{'id': 'id.${version}', 'version': '1'},
                {'id': 'my_${version}', 'version': '2'}
                ]
        select_dependencies(self.constant_values, {}, selected, *defs)
        self.assertEqual(selected, {
            'id.1': (Dependency(defs[0], {
                'id': 'id.1', 'os': None, 'current_os': 'linux'
            }), set()),
            'my_2': (Dependency(defs[1], {
                'id': 'my_2', 'os': None, 'current_os': 'linux'
            }), set())
        })

    def test_select_dependencies_with_filter_on_id(self):
        defs = [{'id': 'id.${version}', 'version': '1'},
                {'id': 'my_${version}', 'version': '2'}
                ]
        filter_ = {'id': r'id\.1'}
        selected = {}
        selected = select_dependencies(self.constant_values, filter_, selected, *defs)
        self.assertEqual(selected, {
            'id.1': (Dependency(defs[0], {
                'id': 'id.1', 'os': None, 'current_os': 'linux'
            }), set())
        })

    def test_select_dependencies_with_filter_on_non_id_field(self):
        defs = [{'id': 'id.${version}', 'version': '1'},
                {'id': 'my_${version}', 'version': '2'}
                ]
        filter_ = {'version': '1'}
        selected = {}
        selected = select_dependencies(self.constant_values, filter_, selected, *defs)
        self.assertEqual(selected, {
            'id.1': (Dependency(defs[0], {
                'id': 'id.1', 'os': None, 'current_os': 'linux', 'version': '1'
            }), set())
        })

    def test_select_dependencies_with_multiple_filters(self):
        defs = [{'id': 'id.${version}', 'version': '1', 'a': '1'},
                {'id': 'my_${version}', 'version': '2', 'a': '1'}
                ]
        filter_ = {'version': '1', 'a': '1'}
        selected = {}
        selected = select_dependencies(self.constant_values, filter_, selected, *defs)
        self.assertEqual(selected, {
            'id.1': (Dependency(defs[0], {
                'id': 'id.1', 'os': None, 'current_os': 'linux', 'version': '1', 'a': '1'
            }), set())
        })

    def test_select_dependencies_with_regex_filter(self):
        defs = [{'id': '1', 'version': '1', 'a': '1a'},
                {'id': '2', 'version': '2', 'a': '1b'},
                {'id': '3', 'version': '2', 'a': '1c'}
                ]
        filter_ = {'version': '[0-9]*', 'a': '1a|1b'}
        selected = {}
        selected = select_dependencies(self.constant_values, filter_, selected, *defs)
        self.assertEqual(selected, {
            '1': (Dependency(defs[0], {
                'id': '1', 'os': None, 'current_os': 'linux', 'version': '1', 'a': '1a'
            }), set()),
            '2': (Dependency(defs[1], {
                'id': '2', 'os': None, 'current_os': 'linux', 'version': '2', 'a': '1b'}),
                set())
        })

if __name__ == '__main__':
    unittest.main()
