"""
Clones a git repo and extracts data.
Activated by a "javadoc" entry in .conf.json, containing the following settings:
    url: Git repository URL (required).
    files: List of filepatterns to copy from the repository (default: all)
"""

import os
import shutil
import urllib2
from os import path
from glob import glob
from devyco.module import Module

JAVADOC_URL = ('http://repository.sonatype.org/service/local/artifact/maven/'
               'redirect?r=central-proxy'
               '&g=%(group)s'
               '&a=%(artifact)s'
               '&v=LATEST&c=javadoc')

HASH_URL = ('https://repo1.maven.org/maven2/'
            '%(group_url)s/'
            '%(artifact)s/'
            '/maven-metadata.xml.md5')

def _up_to_date(group, artifact):
    latest_seen_hash = _get_last_seen_hash()
    print 'latestSeen:'
    print latest_seen_hash
    remote_hash = _get_remote_hash(group, artifact)
    print remote_hash
    with open('.last_seen_hash', 'w') as latest_seen_hash:
        latest_seen_hash.write(remote_hash)
    return remote_hash == latest_seen_hash


def _get_last_seen_hash():
    if not os.path.exists('.last_seen_hash'):
        return None
    with open('.last_seen_hash', 'r') as latest_seen_hash:
        return latest_seen_hash.read()


def _get_remote_hash(group, artifact):
    return urllib2.urlopen(HASH_URL.format(group=group.replace('.', '/'),
                                           artifact=artifact)).read()


class JavaDocModule(Module):
    def __init__(self):
        super(JavaDocModule, self).__init__()
        self._updated = []

    def _run(self):
        conf = self.get_conf('javadoc')
        if conf is None:
            return

        group = conf['groupId']
        artifact = conf['artifactId']

        print 'JavaDoc module!!!'
        print group
        print artifact

        if _up_to_date(group, artifact):
            return

        url = JAVADOC_URL.format(group=group, artifact=artifact)


module = JavaDocModule()

if __name__ == '__main__':
    module.test()
