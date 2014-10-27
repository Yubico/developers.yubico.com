"""
Fetches JavaDoc and publishes from Maven Central.
Activated by a "javadoc" entry in .conf.json, containing the following settings:
    groupId: The Maven groupId for the project
    artifactId: The Maven artifactId for the project
"""

import shutil
from os import path
from urllib2 import urlopen
from StringIO import StringIO
from zipfile import ZipFile
from devyco.module import Module

LAST_SEEN_HASH = 'last_seen_hash'

JAVADOC_ARCHIVE_URL = ('http://repository.sonatype.org/service/local/artifact/maven/'
               'redirect?r=central-proxy'
               '&g={group}'
               '&a={artifact}'
               '&v=LATEST&c=javadoc')

HASH_URL = ('https://repo1.maven.org/maven2/'
            '{group_url}/{artifact}/'
            'maven-metadata.xml.md5')


def _get_last_seen_hash(hash_path):
    if not path.exists(hash_path):
        return None
    with open(hash_path, 'r') as hash_file:
        return hash_file.read()


class JavaDocModule(Module):
    def __init__(self):
        super(JavaDocModule, self).__init__()

    def _run(self):
        conf = self.get_conf('javadoc')
        if conf is None:
            return

        self.group = conf['groupId']
        self.artifact = conf['artifactId']
        self.cache_root = self.cache_dir(self.group + self.artifact, True)

        javadoc_cache_path = path.join(self.cache_root, 'JavaDoc')

        if not self._up_to_date() or not path.exists(javadoc_cache_path):
            url = JAVADOC_ARCHIVE_URL.format(group=self.group,
                                             artifact=self.artifact)
            jarfile = urlopen(url).read()
            zipfile = ZipFile(StringIO(jarfile))
            zipfile.extractall(javadoc_cache_path)

        shutil.copytree(javadoc_cache_path, path.join(self._target, 'JavaDoc'))

    def _up_to_date(self):
        hash_path = path.join(self.cache_root, LAST_SEEN_HASH)
        last_seen_hash = _get_last_seen_hash(hash_path)
        remote_hash = self._get_remote_hash()
        with open(hash_path, 'w') as hash_file:
            hash_file.write(remote_hash)
        return remote_hash == last_seen_hash

    def _get_remote_hash(self):
        url = HASH_URL.format(group_url=self.group.replace('.', '/'),
                              artifact=self.artifact)
        return urlopen(url).read()


module = JavaDocModule()

if __name__ == '__main__':
    module.test()
