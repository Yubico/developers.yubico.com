"""
Fetches JavaDoc and publishes from Maven Central.
Activated by a "javadoc" entry in .conf.json, containing the following settings:
    groupId: The Maven groupId for the project
    artifactId: The Maven artifactId for the project
"""

import os
import shutil
from os import path
from urllib2 import urlopen
from StringIO import StringIO
from zipfile import ZipFile
from devyco.module import Module
from xml.dom import minidom

LOCAL_VERSION = 'local_version'

JAVADOC_ARCHIVE_URL = (
    'http://search.maven.org/remotecontent?'
    'filepath={group_url}/'
    '{artifact}/{version}/'
    '{artifact}-{version}-javadoc.jar')

HASH_URL = ('https://repo1.maven.org/maven2/'
            '{group_url}/{artifact}/'
            'maven-metadata.xml')


def _get_local_version(version_path):
    if not path.exists(version_path):
        return None
    with open(version_path, 'r') as version_file:
        return version_file.read()


class JavaDocModule(Module):
    def __init__(self):
        super(JavaDocModule, self).__init__()

    def _run(self):
        if os.environ.get('OFFLINE'):
            print "OFFLINE set, skip javadoc"
            return

        conf = self.get_conf('javadoc')
        if conf is None:
            return

        self.group_url = conf['groupId'].replace('.', '/')
        self.artifact = conf['artifactId']
        self.cache_root = self.cache_dir(self.group_url + self.artifact, True)

        javadoc_cache_path = path.join(self.cache_root, 'JavaDoc')
        version_path = path.join(self.cache_root, LOCAL_VERSION)

        if not self._up_to_date(version_path) or not path.exists(
                javadoc_cache_path):
            url = JAVADOC_ARCHIVE_URL.format(group_url=self.group_url,
                                             artifact=self.artifact,
                                             version=self.remote_version)
            jarfile = urlopen(url).read()
            zipfile = ZipFile(StringIO(jarfile))
            zipfile.extractall(javadoc_cache_path)
            with open(version_path, 'w') as version_file:
                version_file.write(self.remote_version)

        shutil.copytree(javadoc_cache_path, path.join(self._target, 'JavaDoc'))

    def _up_to_date(self, version_path):
        self._get_remote_version()
        return self.remote_version == _get_local_version(version_path)

    def _get_remote_version(self):
        url = HASH_URL.format(group_url=self.group_url,
                              artifact=self.artifact)
        xml = urlopen(url).read()
        xmldoc = minidom.parseString(xml)
        self.remote_version = xmldoc.getElementsByTagName('latest')[
            0].firstChild.nodeValue


module = JavaDocModule()

if __name__ == '__main__':
    module.test()
