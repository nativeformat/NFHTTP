#!/usr/bin/python
import logging

import unittest
from options import *


class OptionsTestTarget(Target):
    def __init__(self, name, available, default):
        self._name = name
        self.available = available
        self.default = default
        self.opts = {}
        self.parameters = ()
        self.deps = ()

    def name(self):
        return self._name

    def description(self):
        return 'target %s' % self.name()

    def is_available(self):
        return self.available

    def is_default(self):
        return self.default

    def default_opts(self):
        return self.opts.copy()

    def extra_parameters(self):
        return self.parameters

    def dependency_names(self):
        return self.deps


class OptionsTestOptionParameter(OptionParameter):
    def __init__(self, name, require_arg):
        self._name = name
        self._require_arg = require_arg

    def name(self):
        return self._name

    def description(self):
        return 'option %s' % self.name()

    def require_arg(self):
        return self._require_arg

    def update(self, line, arg):
        if 'options' not in line.opts:
            line.opts['options'] = {}
        line.opts['options'][self.name()] = arg


class OptionsTestActionParameter(ActionParameter):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def description(self):
        return 'option %s' % self.name()


class TestOptions(unittest.TestCase):
    def setUp(self):
        self.target1 = OptionsTestTarget('t1', True, True)
        self.target2 = OptionsTestTarget('t2', True, False)
        self.target2.opts = DebugReleaseTarget().default_opts()
        self.target2.parameters += DebugReleaseTarget().extra_parameters()
        self.target2.parameters += (OptionsTestActionParameter('act1'),)
        self.target2.deps = ('foo', 'bar')
        self.target3 = OptionsTestTarget('t3', False, False)
        self.options = Options()
        self.options.name = 'foo'
        self.options.parameters += (self.target1, self.target2, self.target3)
        self.options.parameters += (OptionsTestOptionParameter('opt1', False),
                                    OptionsTestOptionParameter('opt2', True),)

    def test_empty_with_no_default_targets(self):
        self.options = Options()
        self.options.name = 'foo'
        self.options.parameters += (self.target2, self.target3)
        try:
            line = self.options.parse()
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'there are no default available '
                                        'targets')

    def test_empty_with_more_than_one_default_target(self):
        self.target2 = OptionsTestTarget('t2', True, True)
        self.options = Options()
        self.options.name = 'foo'
        self.options.parameters += (self.target1, self.target2)
        try:
            line = self.options.parse()
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'there are more than one default '
                                        'available targets')

    def test_empty(self):
        line = self.options.parse()
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {})

    def test_t1(self):
        line = self.options.parse('t1')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {})

    def test_t2(self):
        line = self.options.parse('t2')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'bar': True, 'foo': True}})

    def test_debug(self):
        try:
            line = self.options.parse('debug')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'unknown args: debug')

    def test_t2_debug(self):
        line = self.options.parse('t2', 'debug')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'bar': True, 'foo': True}})

    def test_t2_release(self):
        line = self.options.parse('t2', 'release')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {'build_type': 'release', 'deps':
                                      {'bar': True, 'foo': True}})

    def test_act1(self):
        try:
            line = self.options.parse('act1')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'unknown args: act1')

    def test_t2_act1(self):
        line = self.options.parse('t2', 'act1')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['act1']))
        self.assertEquals(self.must_do(line), sorted(['act1']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'bar': True, 'foo': True}})

    def test_t1_t2(self):
        try:
            line = self.options.parse('t1', 't2')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'more than one targets specified: '
                                        't1, t2')

    def test_t3(self):
        try:
            line = self.options.parse('t3')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'target t3 is not available')

    def test_help(self):
        line = self.options.parse('help')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['help']))
        self.assertEquals(self.must_do(line), sorted(['help']))
        self.assertEquals(line.opts, {})

    def test_clean(self):
        line = self.options.parse('clean')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean']))
        self.assertEquals(self.must_do(line), sorted(['clean']))
        self.assertEquals(line.opts, {})

    def test_clean_configure(self):
        line = self.options.parse('clean', 'configure')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean',
                                                         'configure']))
        self.assertEquals(self.must_do(line), sorted(['clean', 'deps',
                                                     'configure']))
        self.assertEquals(line.opts, {})

    def test_clean_compile(self):
        line = self.options.parse('clean', 'configure', 'compile')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean', 'configure',
                                                         'compile']))
        self.assertEquals(self.must_do(line), sorted(['clean', 'deps',
                                                     'configure', 'compile']))
        self.assertEquals(line.opts, {})

    def test_clean_test(self):
        line = self.options.parse('clean', 'test')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean', 'test']))
        self.assertEquals(self.must_do(line), sorted(['clean', 'deps',
                                                     'configure', 'compile',
                                                     'test']))
        self.assertEquals(line.opts, {})

    def test_deps(self):
        line = self.options.parse('deps')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['deps']))
        self.assertEquals(self.must_do(line), sorted(['deps']))
        self.assertEquals(line.opts, {})

    def test_t1_deps(self):
        line = self.options.parse('t1', 'deps')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['deps']))
        self.assertEquals(self.must_do(line), sorted(['deps']))
        self.assertEquals(line.opts, {})

    def test_t2_deps(self):
        line = self.options.parse('t2', 'deps')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['deps']))
        self.assertEquals(self.must_do(line), sorted(['deps']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'bar': True, 'foo': True}})

    def test_t2_deps_foo(self):
        line = self.options.parse('t2', 'deps', 'foo')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['deps']))
        self.assertEquals(self.must_do(line), sorted(['deps']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'foo': True}})

    def test_t2_deps_foo_test(self):
        line = self.options.parse('t2', 'deps', 'foo', 'test')
        self.assertIs(line.target, self.target2)
        self.assertEquals(self.is_selected(line), sorted(['deps', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'test']))
        self.assertEquals(line.opts, {'build_type': 'debug', 'deps':
                                      {'foo': True, 'bar': True}})

    def test_configure(self):
        line = self.options.parse('configure')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['configure']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure']))
        self.assertEquals(line.opts, {})

    def test_compile(self):
        line = self.options.parse('compile')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['compile']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile']))
        self.assertEquals(line.opts, {})

    def test_compile_test(self):
        line = self.options.parse('compile', 'test')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'configure',
                                                     'compile', 'test']))
        self.assertEquals(line.opts, {})

    def test_test(self):
        line = self.options.parse('test')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['test']))
        self.assertEquals(self.must_do(line), sorted(['deps', 'test']))
        self.assertEquals(line.opts, {})

    def test_clean_deps_configure_compile_test(self):
        line = self.options.parse('clean', 'deps', 'configure', 'compile',
                                  'test')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean', 'deps',
                                                         'configure',
                                                         'compile', 'test']))
        self.assertEquals(self.must_do(line), sorted(['clean', 'deps',
                                                     'configure', 'compile',
                                                     'test']))
        self.assertEquals(line.opts, {})

    def test_clean_verbose(self):
        self.target1.opts['logger'] = logging.getLogger('foo')
        line = self.options.parse('clean', '--verbose')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean']))
        self.assertEquals(self.must_do(line), sorted(['clean']))
        self.assertIn('logger', line.opts)
        self.assertIs(line.opts['logger'].getEffectiveLevel(), logging.DEBUG)

    def test_clean_bool_option_with_arg(self):
        try:
            line = self.options.parse('clean', '--opt1=value')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'option --opt1 requires no arguments')

    def test_clean_bool_option_without_arg(self):
        line = self.options.parse('clean', '--opt1')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean']))
        self.assertEquals(self.must_do(line), sorted(['clean']))
        self.assertEquals(line.opts, {'options': {'opt1': None}})

    def test_clean_arg_option_with_arg(self):
        line = self.options.parse('clean', '--opt2=value')
        self.assertIs(line.target, self.target1)
        self.assertEquals(self.is_selected(line), sorted(['clean']))
        self.assertEquals(self.must_do(line), sorted(['clean']))
        self.assertEquals(line.opts, {'options': {'opt2': 'value'}})

    def test_clean_arg_option_without_arg(self):
        try:
            line = self.options.parse('clean', '--opt2')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'option --opt2 requires an argument')

    def test_unknown(self):
        try:
            line = self.options.parse('unknown')
            self.fail()
        except Exception as e:
            self.assertEqual(e.message, 'unknown args: unknown')

    def is_selected(self, line):
        return sorted([name for name in line.actions
                      if line.actions[name].is_selected()])

    def must_do(self, line):
        return sorted([name for name in line.actions
                      if line.actions[name].must_do(line)])

    def test_helptext(self):
        # print HelpAction().text(self.options)
        self.assertEquals(HelpAction().text(self.options), (
            'Syntax: foo [targets...] [actions...] [params...]'
            " [options...] (in any order)\n"
            "Targets:\n"
            "  t1        : target t1 (default)\n"
            "  t2        : target t2\n"
            "Actions:\n"
            "  act1      : option act1\n"
            "               available for: t2\n"
            "  clean     : Clean the build directory\n"
            "  compile   : Run the generated build script (default)\n"
            "  configure : Run the build script generator\n"
            "  deps      : Download the dependencies\n"
            "               for t2: bar, foo\n"
            "  help      : Print this help\n"
            "  test      : Run the tests (default)\n"
            "Params:\n"
            "  bar       : Download the dependency bar\n"
            "  debug     : Make a debug build (default)\n"
            "  foo       : Download the dependency foo\n"
            "  release   : Make a release build\n"
            "Options:\n"
            "  --opt1    : option opt1\n"
            "  --opt2=x  : option opt2\n"
            "  --verbose : More output\n"
            "Other targets:\n"
            "  t3        : target t3\n"
            ))

if __name__ == '__main__':
    unittest.main()