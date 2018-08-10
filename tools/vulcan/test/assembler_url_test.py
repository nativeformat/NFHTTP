import os
import sys
import unittest

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, root_path)
from spotify_vulcan.dependencies import Dependency
from spotify_vulcan.assembler_url import UrlAssembler


class TestAssemblerUrl(unittest.TestCase):

    def test_url_assembler_extension_undefined_zip(self):
        url = ('https://foo.com/test/test.zip')
        definition = {'type': 'url', 'url': url}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('zip', self.downloader.format)

    def test_url_assembler_extension_undefined_tar(self):
        url = ('https://foo.com/test/test.tar')
        definition = {'type': 'url', 'url': url}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar', self.downloader.format)

    def test_url_assembler_extension_undefined_tar_gz(self):
        url = ('https://foo.com/test/test.tar.gz')
        definition = {'type': 'url', 'url': url}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar.gz', self.downloader.format)

    def test_url_assembler_extension_undefined_tgz(self):
        url = ('https://foo.com/test/test.tgz')
        definition = {'type': 'url', 'url': url}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar.gz', self.downloader.format)

    def test_url_assembler_extension_undefined_tar_bz2(self):
        url = ('https://foo.com/test/test.tar.bz2')
        definition = {'type': 'url', 'url': url}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar.bz2', self.downloader.format)

    def test_url_assembler_extension_auto_zip(self):
        url = ('https://foo.com/test/test.zip')
        definition = {'type': 'url', 'url': url, 'format': 'auto'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('zip', self.downloader.format)

    def test_url_assembler_extension_auto_tar(self):
        url = ('https://foo.com/test/test.tar')
        definition = {'type': 'url', 'url': url, 'format': 'auto'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar', self.downloader.format)

    def test_url_assembler_extension_auto_tar_gz(self):
        url = ('https://foo.com/test/test.tar.gz')
        definition = {'type': 'url', 'url': url, 'format': 'auto'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar.gz', self.downloader.format)

    def test_url_assembler_extension_auto_tar_bz2(self):
        url = ('https://foo.com/test/test.tar.bz2')
        definition = {'type': 'url', 'url': url, 'format': 'auto'}
        dependency = Dependency(definition, {})
        self.downloader = UrlAssembler(dependency)
        self.assertEquals('tar.bz2', self.downloader.format)

if __name__ == '__main__':
    unittest.main()
