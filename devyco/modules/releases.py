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


SUFFIXES = ['tar', 'gz', 'sig', 'tgz', 'zip', 'exe', 'pkg', 'cap', 'apk']
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
    if classifier:
        return '%s-%s' % (version, classifier)
    return version


class ReleasesModule(Module):

    def _run(self):
        conf = self.get_conf('releases')
        if conf is None:
            return

        target = conf.get('dir', '.')

        files = map(path.basename, self.list_files(relative=target))
        files = [file for file in files if file.endswith('.sig') and
                 file[:-4] in files]
        files.sort(key=lambda s: LooseVersion(version(s)))
        files.reverse()

        entries = []
        for fname in files:
            entries.append({
                'name': remove_suffixes(fname),
                'filename': fname[:-4]
            })

        #artifacts = extract_artifacts(versions, files)

        if not files and conf.get('abortIfEmpty', False):
            return

        tplt = self.get_template('releases')

        outpath = path.join(self._target, target, 'index.partial')
        if not path.isdir(path.dirname(outpath)):
            os.makedirs(path.dirname(outpath))
        with open(outpath, 'w') as outfile:
            outfile.write(tplt.render(releases=entries).encode('utf-8'))


module = ReleasesModule()

if __name__ == '__main__':
    module.test()
