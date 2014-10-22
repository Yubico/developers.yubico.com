"""
Generates a releases page based on release artifacts in a directory.
Activated by a "releases" entry in a .conf.json file, containing the following
settings:
    dir: Location of the release artifacts and resulting index page (defaults
    to the current directory).
    abortIfEmpty: True to abort the page creation if there are no releases
    present.
"""

from os import path
from distutils.version import LooseVersion
from devyco.module import Module
import os


SIG_SUFFIXES = ['sig', 'asc']
SUFFIXES = SIG_SUFFIXES + ['tar', 'gz', 'tgz', 'zip', 'exe', 'pkg', 'cap', 'apk']
CLASSIFIERS = ['win', 'win32', 'win64', 'mac']


def remove_suffixes(part):
    split = part.rsplit('.', 1)
    if len(split) == 2 and split[1] in SUFFIXES:
        part = remove_suffixes(split[0])
    return part


def remove_classifier(part):
    split = part.rsplit('-', 1)
    if len(split) == 2 and split[1] in CLASSIFIERS:
        return split[0], split[1]
    return part, None


def version(filename):
    part = remove_suffixes(filename)
    part, classifier = remove_classifier(part)
    version = part.rsplit('-', 1)[1]
    return version, classifier


def version_with_classifier(filename):
    vers, classifier = version(filename)
    if classifier:
        return '%s-%s' % (vers, classifier)
    return vers


def extract_versions(files):
    versions = []
    for fname in files:
        v, classifier = version(fname)
        if v not in versions:
            versions.append(v)
    versions.sort(key=LooseVersion, reverse=True)
    return versions


def is_sig(fname):
    for suffix in SIG_SUFFIXES:
        if fname.endswith('.' + suffix):
            return True
    return False


def get_sig(fname, files):
    for suffix in SIG_SUFFIXES:
        sig = '%s.%s' % (fname, suffix)
        if sig in files:
            return sig
        else:
            print sig, "not in", files
    return None


def extract_files(v, files):
    matches = []
    for fname in files:
        if version(fname)[0] == v and not is_sig(fname):
            matches.append({
                "filename": fname,
                "sig": get_sig(fname, files)
            })
    matches.sort(key=lambda x: LooseVersion(version_with_classifier(x['filename'])))
    return matches


class ReleasesModule(Module):

    def _run(self):
        conf = self.get_conf('releases')
        if conf is None:
            return

        target = conf.get('dir', '.')

        all_files = map(path.basename, self.list_files(relative=target))
        if not all_files and conf.get('abortIfEmpty', False):
            return

        versions = extract_versions(all_files)

        entries = []
        for v in versions:
            entries.append({
                "version": v,
                "files": extract_files(v, all_files)
            })

        tplt = self.get_template('releases')

        outpath = path.join(self._target, target, 'index.partial')
        if not path.isdir(path.dirname(outpath)):
            os.makedirs(path.dirname(outpath))
        with open(outpath, 'w') as outfile:
            outfile.write(tplt.render(releases=entries).encode('utf-8'))


module = ReleasesModule()

if __name__ == '__main__':
    module.test()
