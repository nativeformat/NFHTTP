#!/usr/bin/env python
# coding=utf-8
import argparse
import json
import sys
import allowed
from xml.etree import ElementTree


class JSONParserFailure(Exception):
    pass


class Map(dict):
    def __init__(self, filename=None):
        dict.__init__(self)

        if filename is not None:
            self.load_map(filename)

    def load_map(self, filename):
        try:
            blob = self._load_json(filename)
        except JSONParserFailure:
            # Doesn't look like a valid JSON, try XML.
            blob = self._load_xml(filename)

        self.clear()
        self.update(blob)

    def _load_xml(self, filename):
        raise NotImplemented()

    def _load_json(self, filename):
        with open(filename, 'rb') as fp:
            try:
                blob = json.load(fp)
            except ValueError:
                raise JSONParserFailure
            return {k.lower(): v for k, v in blob.items()}


class TestsuiteFeatureMap(Map):
    def _load_xml(self, filename):
        xml_root = ElementTree.parse(filename).getroot()
        return {tag.get('name').lower(): tag.get('feature')
                for tag in xml_root}


class FeatureSquadMap(Map):
    def _load_xml(self, filename):
        xml_root = ElementTree.parse(filename).getroot()
        return {tag.get('name').lower(): tag.get('owner') for tag in xml_root}


class FeatureJiraFeatureMap(Map):
    def _load_xml(self, filename):
        xml_root = ElementTree.parse(filename).getroot()
        return {tag.get('name').lower(): tag.get('jirafeature')
                for tag in xml_root}


class PackageOwnerMap(Map):
    pass


class Decorator(object):
    def __init__(self,
                 junit_xml,
                 testsuite_feature_map,
                 feature_squad_map,
                 feature_jira_feature,
                 package_owner_map=None,
                 test_type='UNKNOWN',
                 test_phase='UNKNOWN',
                 **kw):
        self.junit_xml = junit_xml
        self.testsuite_feature_map = testsuite_feature_map
        self.feature_squad_map = feature_squad_map
        self.feature_jira_feature = feature_jira_feature
        self.package_owner_map = package_owner_map
        self.test_type = 'UNKNOWN' if test_type is None \
            or test_type not in allowed.TEST_TYPES else test_type
        self.test_phase = 'UNKNOWN' if test_phase is None \
            or test_phase not in allowed.TEST_PHASES else test_phase
        self.additional_args = kw
        self.package_squad_count = 0

    def decorate(self):
        xml_tree = ElementTree.parse(self.junit_xml)
        xml_root = xml_tree.getroot()

        iterables = iter(xml_root)
        if xml_root.tag == 'testsuite':
            # This is a single testsuite XML file
            iterables = (xml_root,)

        # Modify xml_root inplace
        for testsuite in iterables:
            if not testsuite.tag == 'testsuite':
                continue

            testsuite_name = testsuite.get('name')
            feature = self.testsuite_feature_map.get(testsuite_name.lower(),
                                                     "UNKNOWN")
            squad = self.feature_squad_map.get(feature.lower(), "UNKNOWN")
            jira_feature = self.feature_jira_feature.get(feature.lower(),
                                                         "UNKNOWN")

            properties_node = testsuite.find('properties')
            append_properties = False

            if properties_node is None:
                properties_node = ElementTree.Element('properties')
                append_properties = True

            if squad == 'UNKNOWN' and self.package_owner_map:
                # testsuite_name is expected to be of the form:
                #   com.spotify.package.TestClassName
                # we want to extract the "com.spotify.package" part for mapping
                # to an owner using the (optional) provided package_owner_map
                nameparts = testsuite_name.lower().split('.')
                nameparts.pop()
                package = '.'.join(nameparts)
                if package in self.package_owner_map \
                        and self.package_owner_map[package]:
                    squad = self.package_owner_map[package]

            node = self.xml_node_properties(
                properties_node,
                feature=feature,
                owner=squad,
                jirafeature=jira_feature,
                type=self.test_type,
                phase=self.test_phase,
                **self.additional_args)

            if append_properties:
                testsuite.append(node)

        return ElementTree.tostring(xml_root)

    def xml_node_properties(self, node, **kw):
        for key, value in kw.items():
            node.append(
                self.xml_node_property(name='spotify.' + key, value=value))
        return node

    def xml_node_property(self, name, value):
        node = ElementTree.Element('property')
        node.set('name', name)
        node.set('value', value)
        return node


def main():
    p = argparse.ArgumentParser(
        description='Decorates junit.xml report with additional Spotify '
                    'metadata such as feature names and ownership. '
                    'The decorated xml content is printed to STDOUT.')

    p.add_argument('junit_xml', metavar='JUNIT_XML',
                   help='Junit XML report to be decorated')

    p.add_argument('-t', '--testsuite-feature-map', required=True,
                   metavar="FILE",
                   dest='testsuite_feature',
                   help='File containing a mapping between testsuites and '
                        'corresponding features (both XML and JSON are '
                        'supported)')

    p.add_argument('-s', '--feature-squad-map', required=True, metavar="FILE",
                   dest='feature_squad',
                   help='File containing a mapping between features and squads'
                         ' that own them (both XML and JSON are supported)')

    p.add_argument('-j', '--feature-jira-feature', metavar="FILE",
                   dest='feature_jira_feature',
                   help='File containing a mapping between features and '
                        'jira-features (both XML and JSON are supported)')

    p.add_argument('-i', '--inplace', action='store_true',
                   dest='modify_inplace',
                   help='Modify the XML file in-place, without printing the '
                        'contents out (this operation is NOT idempotent, so '
                        'use carefully)')

    p.add_argument('-p', '--package-owner-map', action='store',
                   dest='package_owners',
                   help='JSON file containing a mapping of Java packages to'
                        ' owner names. This will be used as a fallback if the'
                        ' test lacks a feature annotation.')

    # See Schema:
    # https://docs.google.com/document/d/1P0qe5e3TYu5Y3NO8eo2t1Af_zHYLopCdqCR1O23rRQI
    p.add_argument('--test-type', default='UNKNOWN', dest='test_type',
                   help='Type of the test: '
                   'unit, integration, e2e, other, UNKNOWN')

    p.add_argument('--test-phase', default='UNKNOWN', dest='test_phase',
                   help='Phase of the tests being run: '
                        'premerge, postmerge, supa, other, UNKNOWN')

    args = p.parse_args()

    testsuite_feature_map = \
        TestsuiteFeatureMap(filename=args.testsuite_feature)
    feature_squad_map = FeatureSquadMap(filename=args.feature_squad)
    feature_jira_feature = \
        FeatureJiraFeatureMap(filename=args.feature_jira_feature)
    package_owner_map = {}
    if args.package_owners:
        package_owner_map = PackageOwnerMap(args.package_owners)

    decorator = Decorator(
        junit_xml=args.junit_xml,
        testsuite_feature_map=testsuite_feature_map,
        feature_squad_map=feature_squad_map,
        feature_jira_feature=feature_jira_feature,
        package_owner_map=package_owner_map,
        test_type=args.test_type,
        test_phase=args.test_phase)

    decorated_xml = decorator.decorate()

    out_fp = sys.stdout
    if args.modify_inplace:
        out_fp = open(args.junit_xml, 'w')

    out_fp.write(decorated_xml)

    if args.modify_inplace:
        out_fp.close()


if __name__ == '__main__':
    main()
