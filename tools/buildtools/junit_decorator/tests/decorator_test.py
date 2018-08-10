import contextlib
import os
import tempfile
import unittest
import allowed

from lxml import etree

import decorator


xml_junit = '''\
<testsuites failures="0" tests="6762">
    <testsuite failures="0" name="com.spotify.package1.NSDateSPTAccountInterval" tests="4">
        <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan24HoursAgoIsTruthy" time="0.011" />
        <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan4DaysAgoIsTruthy" time="0.010" />
    </testsuite>
    <testsuite failures="0" name="com.spotify.package2.SPTAdRewardTests" tests="2">
        <testcase classname="SPTAdRewardTests" name="testRewardTime" time="0.005" />
        <testcase classname="SPTAdRewardTests" name="testRewardUnknown" time="0.005" />
    </testsuite>
</testsuites>
'''

xml_junit_with_properties = '''\
<testsuites failures="0" tests="6762">
    <testsuite failures="0" name="com.spotify.package1.NSDateSPTAccountInterval" tests="4">
        <properties/>
        <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan24HoursAgoIsTruthy" time="0.011" />
        <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan4DaysAgoIsTruthy" time="0.010" />
    </testsuite>
    <testsuite failures="0" name="com.spotify.package2.SPTAdRewardTests" tests="2">
        <testcase classname="SPTAdRewardTests" name="testRewardTime" time="0.005" />
        <testcase classname="SPTAdRewardTests" name="testRewardUnknown" time="0.005" />
    </testsuite>
</testsuites>
'''

xml_junit_testsuite = '''\
<testsuite failures="0" name="NSDateSPTAccountInterval" tests="4">
    <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan24HoursAgoIsTruthy" time="0.011" />
    <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan4DaysAgoIsTruthy" time="0.010" />
</testsuite>
'''

xml_junit_testsuite_with_properties = '''\
<testsuite failures="0" name="NSDateSPTAccountInterval" tests="4">
    <properties/>
    <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan24HoursAgoIsTruthy" time="0.011" />
    <testcase classname="NSDateSPTAccountInterval" name="testDateMoreThan4DaysAgoIsTruthy" time="0.010" />
</testsuite>
'''

testsuite_feature = {
    "com.spotify.package1.nsdatesptaccountinterval": "account",
    "com.spotify.package2.sptadrewardtests": "ads",
}

feature_squad = {
    "account": "clippy",
    "ads": "CREAM",
}

feature_jira_feature = {
    "account": "Jira Account",
    "ads": "Ads Products",
}

feature_jira_feature_missing = {
    "account": "Jira Account",
    "not_presents": "Not Here",
}

feature_jira_feature_empty = {
    "account": "Jira Account",
    "ads": "",
}

testsuite_feature_one = {
    "sptadrewardtests": "ads",
}

feature_squad_one = {
    "account": "clippy",
}

partial_package_owner = {
    "com.spotify.package1": "owner1"
}

full_package_owner = {
    "com.spotify.package1": "owner1",
    "com.spotify.package2": "owner2"
}

full_package_owner_empty = {
    "com.spotify.package1": "owner1",
    "com.spotify.package2": ""
}


class DecoratorTest(unittest.TestCase):
    @contextlib.contextmanager
    def write_xml(self, payload):
        map_file = tempfile.NamedTemporaryFile()

        map_file.write(payload)
        map_file.flush()

        yield os.path.abspath(map_file.name)

        map_file.close()

    def _test_xml_decoration(
            self, xml, testsuite_feature_map, feature_squad_map,
            feature_jira_feature, test_type=None, test_phase=None,
            extra_keys=tuple(), extra_values=tuple(), expected_owners=None,
            **kw):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml, testsuite_feature_map, feature_squad_map,
            feature_jira_feature, test_type, test_phase,
            extra_keys, extra_values, **kw)
        self._validate(
            props, testsuite, prop_tags,
            testsuite_feature_map, feature_squad_map,
            feature_jira_feature, extra_keys, expected_owners)
        return (props, testsuite, prop_tags)

    def _get_props_from_xml(
            self, xml, testsuite_feature_map, feature_squad_map,
            feature_jira_feature, test_type=None, test_phase=None,
            extra_keys=tuple(), extra_values=tuple(), **kw):
        with self.write_xml(xml) as name:
            d = decorator.Decorator(
                junit_xml=name,
                testsuite_feature_map=testsuite_feature_map,
                feature_squad_map=feature_squad_map,
                feature_jira_feature=feature_jira_feature,
                test_type=test_type,
                test_phase=test_phase,
                **kw)

            decorated_xml = d.decorate()

            tree = etree.fromstring(decorated_xml)

            xpath_root = '/testsuite'
            if tree.tag == 'testsuites':
                xpath_root = '/testsuites' + xpath_root

            property_tags = tree.xpath(xpath_root + '/properties/property')
            testsuite_tags = tree.xpath(xpath_root)

            properties_tags = tree.xpath(xpath_root + '/properties')

        return (properties_tags, testsuite_tags, property_tags)

    def _validate(self, properties_tags, testsuite_tags, property_tags,
                  testsuite_feature_map, feature_squad_map,
                  feature_jira_feature, extra_keys, expected_owners):
        self.assertEqual(
            len(properties_tags),
            len(testsuite_tags),
            'There must be 1 properties tags per each testsuite in '
            'decorated XML but found {0}'.format(len(properties_tags)))
        self.assertTrue(
            testsuite_tags, 'Testsuite tags collection cannot be empty')
        self.assertTrue(
            property_tags, 'Property tags collection cannot be empty')
        allowed_features = testsuite_feature_map.values() + ['UNKNOWN']
        allowed_owners = feature_squad_map.values() + ['UNKNOWN']
        if expected_owners:
            allowed_owners += expected_owners
        allowed_owners = list(set(allowed_owners))
        allowed_jira_features = feature_jira_feature.values() + ['UNKNOWN']
        allowed_keys = ['spotify.' + k for k in [
            'feature', 'jira_feature', 'owner', 'type', 'phase']] \
            + list(extra_keys)
        num_props = len(allowed_keys)

        self.assertEqual(
            len(property_tags),
            # Currently 5 required properties
            len(testsuite_tags) * num_props,
            'There must be {0} property tags per each testsuite in '
            'decorated XML, but had {1}: {2}. '
            ''.format(
                num_props, len(property_tags), property_tags))

        property_values = {}

        def validate_property(property_tag, allowed_values):
            name = property_tag.attrib['name']
            value = property_tag.attrib['value']
            self.assertTrue(
                name in allowed_keys,
                'Only predefined properties should be in decorated XML. '
                '\"{0}\"" was not in properties \"{1}\"'
                ''.format(name, allowed_keys))
            self.assertTrue(
                value in allowed_values,
                'Only predefined values should be in decorated XML. '
                '\"{0}\" was not in values \"{1}\"'
                ''.format(value, allowed_values))
            if name not in property_values:
                property_values[name] = []
            property_values[name].append(value)

        for property_tag in property_tags:
            prop = property_tag.attrib['name']
            if prop == 'spotify.feature':
                validate_property(property_tag, allowed_features)
            elif prop == 'spotify.owner':
                validate_property(property_tag, allowed_owners)
            elif prop == 'spotify.jira_feature':
                validate_property(property_tag, allowed_jira_features)
            elif prop == 'spotify.type':
                validate_property(property_tag, allowed.TEST_TYPES)
            elif prop == 'spotify.phase':
                validate_property(property_tag, allowed.TEST_PHASES)
            else:
                self.assertTrue(
                    prop.startswith('spotify.'))
        if expected_owners:
            self.assertListEqual(
                property_values['spotify.owner'],
                expected_owners)

    def test_decorate_valid(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature=feature_jira_feature,
            feature_squad_map=feature_squad)
        self._test_xml_decoration(
            xml=xml_junit_with_properties,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature=feature_jira_feature,
            feature_squad_map=feature_squad)

    def test_decorate_valid_without_jira_feature(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature={},
            feature_squad_map=feature_squad,
            extra_values=['UNKNOWN'])
        self._test_xml_decoration(
            xml=xml_junit_with_properties,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature={},
            feature_squad_map=feature_squad,
            extra_values=['UNKNOWN'])

    def test_decorate_valid_single_testsuite(self):
        self._test_xml_decoration(
            xml=xml_junit_testsuite,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature=feature_jira_feature,
            feature_squad_map=feature_squad)
        self._test_xml_decoration(
            xml=xml_junit_testsuite_with_properties,
            testsuite_feature_map=testsuite_feature,
            feature_jira_feature=feature_jira_feature,
            feature_squad_map=feature_squad)

    def test_decorate_unknown_squad(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad_one,
            feature_jira_feature=feature_jira_feature,
            extra_values=['UNKNOWN'])

    def test_decorate_unknown_feature(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature_one,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            extra_values=['UNKNOWN'])

    def test_decorate_valid_extra_properties(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            extra_keys=['foo'],
            extra_values=['bar'],
            foo='bar')

    def test_decorate_with_allowed_test_type(self):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            test_type='unit')
        for p in prop_tags:
            if p.attrib['name'] == 'spotify.type':
                self.assertTrue(p.attrib['value'] == 'unit')

    def test_decorate_with_allowed_test_phase(self):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            test_phase='premerge')
        for p in prop_tags:
            if p.attrib['name'] == 'spotify.phase':
                self.assertTrue(p.attrib['value'] == 'premerge')

    def test_decorate_with_disallowed_test_type_should_be_unknown(self):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            test_type='Friday')
        self.assertFalse('Friday' in [p.attrib['value'] for p in prop_tags])
        for p in prop_tags:
            if p.attrib['name'] == 'spotify.type':
                self.assertTrue(p.attrib['value'] == 'UNKNOWN')

    def test_decorate_with_disallowed_test_phase_should_be_unknown(self):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            test_phase='whatever')
        self.assertFalse('whatever' in [p.attrib['value'] for p in prop_tags])
        for p in prop_tags:
            if p.attrib['name'] == 'spotify.phase':
                self.assertTrue(p.attrib['value'] == 'UNKNOWN')

    def test_decorate_test_type_defaults_to_unknown(self):
        props, testsuite, prop_tags = self._get_props_from_xml(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature)
        for p in prop_tags:
            if p.attrib['name'] == 'spotify.type' or \
               p.attrib['name'] == 'spotify.phase':
                    self.assertTrue(p.attrib['value'] == 'UNKNOWN')

    def test_decorate_valid_jira_feature(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature)

    def test_decorate_valid_jira_feature_with_one_test_case(self):
        self._test_xml_decoration(
            xml=xml_junit_testsuite,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature)

    def test_decorate_valid_jira_feature_with_missing_jira_feature(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature_missing,
            extra_values=['UNKNOWN'])

    def test_decorate_valid_jira_feature_with_empty_jira_feature(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature_missing,
            extra_values=['UNKNOWN'])

    def test_decorate_with_partial_package_owner_mapping(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map={},
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            package_owner_map=partial_package_owner,
            expected_owners=['owner1', 'UNKNOWN'])

    def test_decorate_with_full_package_owner_mapping(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map={},
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            package_owner_map=full_package_owner,
            expected_owners=['owner1', 'owner2'])

    def test_decorate_testsuite_feature_supercedes_package_owner(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map=testsuite_feature,
            feature_squad_map=feature_squad,
            feature_jira_feature=feature_jira_feature,
            package_owner_map=full_package_owner,
            expected_owners=['clippy', 'CREAM'])

    def test_decorate_with_owner_mapping_containing_empty_value(self):
        self._test_xml_decoration(
            xml=xml_junit,
            testsuite_feature_map={},
            feature_squad_map={},
            feature_jira_feature=feature_jira_feature,
            package_owner_map=full_package_owner_empty,
            expected_owners=['owner1', 'UNKNOWN'])
