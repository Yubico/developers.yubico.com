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
from glob import glob
from devyco.module import Module


class ProjectModule(Module):

    def _run(self):
        conf = self.get_conf('project')
        if conf is None:
            return

        self._move_index(conf)
        self._move_docs(conf)

    def _move_index(self, conf):
        source = path.join(self._target, conf.get('index', 'README'))
        target = path.join(self._target, 'index.adoc')
        shutil.move(source, target)

    def _move_docs(self, conf):
        documents = conf.get('documents', 'doc/*')
        for doc in glob(path.join(self._target, documents)):
            target = path.join(self._target, path.basename(doc))
            shutil.move(doc, target)


module = ProjectModule()

if __name__ == '__main__':
    module.test()
