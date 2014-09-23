"""
Generates data from a project directory.
Activated by a "project" entry in a .conf.json file, containing the following
settings:
    index: File to use as index page (optional, defaults to "README")
    documents: File pattern of documents (optional, defaults to "doc/*")

TODO: Read BLURB file and add additional stuff to index page (GitHub, TravisCI,
license, etc.).
"""

import shutil
from os import path
from distutils.version import LooseVersion
from jinja2 import Environment, FileSystemLoader
from devyco.module import Module, noext


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
        if not hasattr(self, '_env'):
            self._env = Environment(
                loader=FileSystemLoader(self._context['basedir']))

        conf = self.get_conf('releases')
        if conf is None:
            return

        files = map(path.basename, self.list_files())
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

        tplt = self._env.get_template('releases.template')

        with open(path.join(self._target, 'index.partial'), 'w') as outfile:
            outfile.write(tplt.render(releases=entries).encode('utf-8'))


module = ReleasesModule()

if __name__ == '__main__':
    module.test()
