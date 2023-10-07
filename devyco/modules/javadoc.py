"""
Fetches JavaDoc and publishes from Maven Central.
Activated by a "javadoc" entry in .conf.json, containing the following settings:
    groupId: The Maven groupId for the project
    artifactId: The Maven artifactId for the project
"""

import json
import os
import re
import semver
import shutil
from os import path
from urllib2 import urlopen, URLError
from StringIO import StringIO
from zipfile import ZipFile
from devyco.module import Module
from xml.dom import minidom
from semver import VersionInfo

MAX_CONSECUTIVE_TIMEOUTS = 10  # Accept occasional timeouts from Maven Central since this part of their API is not very stable.

LOCAL_VERSION = 'local_version'
CONSECUTIVE_TIMEOUTS = 'consecutive_timeouts'

JAVADOC_ARCHIVE_URL = (
    'http://search.maven.org/remotecontent?'
    'filepath={group_url}/'
    '{artifact}/{version}/'
    '{artifact}-{version}-javadoc.jar')

HASH_URL = ('https://repo1.maven.org/maven2/'
            '{group_url}/{artifact}/'
            'maven-metadata.xml')

"""
Stores single values in a file.
"""
class FileStore(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        if not path.exists(self.file_path):
            return None
        with open(self.file_path, 'r') as f:
            return f.read()

    def write(self, value):
        with open(self.file_path, 'w') as f:
            f.write(str(value))


class JavaDocModule(Module):
    def __init__(self):
        super(JavaDocModule, self).__init__()

    def _run(self):
        conf = self.get_conf('javadoc')
        if conf is None:
            return

        if os.environ.get('OFFLINE'):
            print 'OFFLINE set, skip javadoc'
            return

        self.group_url = conf['groupId'].replace('.', '/')
        self.artifact = conf['artifactId']
        self.cache_root = self.cache_dir(self.group_url + self.artifact, True)

        javadoc_cache_path = path.join(self.cache_root, 'JavaDoc')
        version_store = FileStore(path.join(self.cache_root, LOCAL_VERSION))
        consecutive_timeouts_store = FileStore(path.join(self.cache_root, CONSECUTIVE_TIMEOUTS))

        try:
            up_to_date = self._up_to_date(version_store)
            consecutive_timeouts = 0
        except URLError as e:
            consecutive_timeouts = int(
                consecutive_timeouts_store.read() or 0) + 1
            if consecutive_timeouts > MAX_CONSECUTIVE_TIMEOUTS:
                raise IOError(
                    'Fetching of Maven Central URL has failed all of the last %s builds: %s' % (
                        consecutive_timeouts, e))
            up_to_date = True
        consecutive_timeouts_store.write(consecutive_timeouts)

        if not up_to_date or not path.exists(javadoc_cache_path):
            if conf.get('all_versions', False) == True:
                artifact_ids = conf.get('artifactIds', [self.artifact])

                versions = {}

                for artifact_id in artifact_ids:
                    artifact_versions = self.get_versions(artifact_id)

                    for version in artifact_versions:
                        versions[version] = versions.get(version, set())
                        versions[version].add(artifact_id)

                versions = {
                    version: self._override_artifact_ids(conf, version, artifact_ids)
                    for version, artifact_ids in versions.items()
                }

                latest_version = max(versions.keys(), key=VersionInfo.parse)
                latest_versions = {
                    artifact_id: latest_version
                    for artifact_id in versions[latest_version]
                }

                for version, version_artifact_ids in versions.items():
                    for artifact_id in version_artifact_ids:
                        self._extract_javadoc(
                            path.join(javadoc_cache_path, artifact_id, version),
                            artifact_id,
                            version)
                for artifact_id in latest_versions.keys():
                    self._extract_javadoc(
                        path.join(javadoc_cache_path, artifact_id, 'latest'),
                        artifact_id,
                        latest_version)

                outpath = path.join(javadoc_cache_path, 'index.partial')
                tplt = self.get_template('javadoc-versions')
                with open(outpath, 'w') as outfile:
                    outfile.write(tplt.render(
                                latest_versions=sorted(latest_versions.items()),
                                versions=sorted(
                                    [
                                        (v, sorted(aids))
                                        for v, aids in versions.items()
                                    ],
                                    key=lambda pair: VersionInfo.parse(pair[0]),
                                    reverse=True),
                                ).encode('utf-8'))

                with open(path.join(javadoc_cache_path, '.conf.json'), 'w') as excludefile:
                    json.dump({'exclude': artifact_ids}, excludefile)

            else:
                self._extract_javadoc(javadoc_cache_path, self.artifact, self.remote_version)

            version_store.write(self.remote_version)

        shutil.copytree(javadoc_cache_path, path.join(self._target, 'JavaDoc'))

    def _override_artifact_ids(self, conf, version, artifact_ids):
        """
        Override the `artifact_ids` if `version` matches any pattern in the `artifactIdVersions` config.

        Consider each `(pattern, override_artifact_ids)` in
        `artifactIdVersions`. Assume that `pattern` is a `semver.match`
        pattern. If `version` matches any `pattern`, then return the
        corresponding `override_artifact_ids`. If no pattern matches, return
        `artifact_ids` unchanged.

        In addition to the syntax documented in `semver.match()`, the `pattern`
        may contain semicolons to separate multiple patterns. In this case the
        version must match all the constituent patterns in `patterns` to be
        considered to match `pattern`.

        The set of `pattern`s must be disjoint - `version` must match zero or one `pattern`.
        """
        result = artifact_ids
        version_pattern_matches = 0

        for version_pattern, version_artifact_ids in conf.get('artifactIdVersions', {}).items():
            if all(semver.match(version, vp) for vp in version_pattern.split(';')):
                version_pattern_matches += 1
                if version_pattern_matches > 1:
                    raise AssertionError(
                        "version {version} of {aid} matches more than one artifactIdVersions pattern"
                        .format(version=version, aid=self.artifact))

                result = version_artifact_ids
        return result

    def _extract_javadoc(self, output_path, artifact_id, version):
        url = JAVADOC_ARCHIVE_URL.format(group_url=self.group_url,
                                         artifact=artifact_id,
                                         version=version)
        jarfile = urlopen(url).read()
        zipfile = ZipFile(StringIO(jarfile))
        zipfile.extractall(output_path)

    def _up_to_date(self, version_store):
        self._get_remote_version()
        return self.remote_version == version_store.read()

    def _get_remote_version(self):
        url = HASH_URL.format(group_url=self.group_url,
                              artifact=self.artifact)
        xml = urlopen(url).read()
        xmldoc = minidom.parseString(xml)
        self.remote_version = xmldoc.getElementsByTagName('latest')[
            0].firstChild.nodeValue

    def get_versions(self, artifact_id):
        url = HASH_URL.format(group_url=self.group_url,
                              artifact=artifact_id)
        xml = urlopen(url).read()
        xmldoc = minidom.parseString(xml)
        versions = [v.firstChild.nodeValue
                    for v in xmldoc.getElementsByTagName('version')]
        versions = sorted([v for v in versions
                           if re.match(r"^\d+\.\d+\.\d+$", v)],
                          key=VersionInfo.parse)
        return versions


module = JavaDocModule()

if __name__ == '__main__':
    module.test()
