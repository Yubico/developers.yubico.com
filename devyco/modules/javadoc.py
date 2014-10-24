"""
Clones a git repo and extracts data.
Activated by a "git" entry in .conf.json, containing the following settings:
    url: Git repository URL (required).
    files: List of filepatterns to copy from the repository (default: all)

The "git" entry can also be a list of objects containing the settings above if
multiple repositories should be clones.
"""

import os
import shutil
import urllib2
from os import path
from glob import glob
from devyco.module import Module


class JavaDocModule(Module):

    def __init__(self):
        super(JavaDocModule, self).__init__()
        self._updated = []

    def _run(self):
        conf = self.get_conf('javadoc')
        if conf is None:
            return

        self.group = conf['groupId']
        self.artifact = conf['artifactId']

        print 'JavaDoc module!!!'
        print self.group
        print self.artifact

        latestSeenHash = self._getLastSeenHash()
        
        print 'latestSeen:'
        print latestSeenHash

        remoteHash = self._getRemoteHash()
        print remoteHash
        
        with open('.last_seen_hash', 'w') as latest_seen_hash:
            latest_seen_hash.write(remoteHash)



    def _getRemoteHash(self):
        url = 'https://repo1.maven.org/maven2/' + self.group.replace('.', '/') + '/' + self.artifact + '/maven-metadata.xml.md5'
        return urllib2.urlopen(url).read()

    def _getLastSeenHash(self):
        if not os.path.exists('.last_seen_hash'):
            return None
        with open('.last_seen_hash', 'r') as latest_seen_hash:
            return latest_seen_hash.read()


module = JavaDocModule()

if __name__ == '__main__':
    module.test()
