import contextlib
import os
import tempfile
import unittest

import decorator


# Reference dicts. The keys should be lowercase.
testsuite_feature = {
    "avaudiosessionroutedescriptionsptcarplayadditionstest": "carplay",
    "adfeaturetests": "ads",
    "adsfeatureimplementationtest": "ads",
    "albumfeatureimplementationtest": "album",
}

feature_squad = {
    "glue": "HUBBLE",
    "sptaudiopreview": "iOSInfra",
    "sptcollectionkit": "Fesk",
    "sptcosmosutility": "Fesk"
}

feature_jira_feature = {
    "party": "Party [Party]",
    "playlist": "Playlist [Playlist]"
}

# Test file content
xml_testsuite_feature = '''\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<testsuites>
<testsuite feature="carplay" name="AVAudioSessionRouteDescriptionSPTCarPlayAdditionsTest"/>
<testsuite feature="ads" name="AdFeatureTests"/>
<testsuite feature="ads" name="AdsFeatureImplementationTest"/>
<testsuite feature="album" name="AlbumFeatureImplementationTest"/>
</testsuites>
'''

xml_feature_squad = '''\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<features>
<feature name="GLUE" owner="HUBBLE" />
<feature name="SPTAudioPreview" owner="iOSInfra" />
<feature name="SPTCollectionKit" owner="Fesk" />
<feature name="SPTCosmosUtility" owner="Fesk" />
</features>
'''

xml_feature_jira_feature = '''\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<jirafeatures>
<jirafeature name="PARTY" jirafeature="Party [Party]" />
<jirafeature name="PLAYLIST" jirafeature="Playlist [Playlist]" />
</jirafeatures>
'''

json_testsuite_feature = '''\
{
    "AVAudioSessionRouteDescriptionSPTCarPlayAdditionsTest": "carplay",
    "AdFeatureTests": "ads",
    "AdsFeatureImplementationTest": "ads",
    "AlbumFeatureImplementationTest": "album"
}
'''

json_feature_squad = '''\
{
    "GLUE": "HUBBLE",
    "SPTAudioPreview": "iOSInfra",
    "SPTCollectionKit": "Fesk",
    "SPTCosmosUtility": "Fesk"
}
'''

json_feature_jira_feature = '''\
{
    "PARTY": "Party [Party]",
    "playlist": "Playlist [Playlist]"
}
'''


class MapTest(unittest.TestCase):
    @contextlib.contextmanager
    def write_map(self, payload):
        map_file = tempfile.NamedTemporaryFile()

        map_file.write(payload)
        map_file.flush()

        yield os.path.abspath(map_file.name)

        map_file.close()

    def test_load_xml_testsuite_feature(self):
        with self.write_map(xml_testsuite_feature) as name:
            result = decorator.TestsuiteFeatureMap(name)
            self.assertDictEqual(testsuite_feature, result,
                "Reference dict must match parsed XML dict")

    def test_load_xml_feature_squad(self):
        with self.write_map(xml_feature_squad) as name:
            result = decorator.FeatureSquadMap(name)
            self.assertDictEqual(feature_squad, result,
                "Reference dict must match parsed XML dict")

    def test_load_xml_feature_jira_feature(self):
        with self.write_map(xml_feature_jira_feature) as name:
            result = decorator.FeatureJiraFeatureMap(name)
            print result
            self.assertDictEqual(feature_jira_feature, result,
                "Reference dict must match parsed XML dict")

    def test_load_json_testsuite_feature(self):
        with self.write_map(json_testsuite_feature) as name:
            result = decorator.TestsuiteFeatureMap(name)
            self.assertDictEqual(testsuite_feature, result,
                "Reference dict must match parsed JSON dict")

    def test_load_json_feature_squad(self):
        with self.write_map(json_feature_squad) as name:
            result = decorator.FeatureSquadMap(name)
            self.assertDictEqual(feature_squad, result,
                "Reference dict must match parsed JSON dict")

    def test_load_json_feature_jira_feature(self):
        with self.write_map(json_feature_jira_feature) as name:
            result = decorator.FeatureJiraFeatureMap(name)
            self.assertDictEqual(feature_jira_feature, result,
                "Reference dict must match parsed JSON dict")
