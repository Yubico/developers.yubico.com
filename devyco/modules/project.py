"""
Generates data from a project directory.
Activated by a .project.json file in a content directory, containing the following
settings:
    index: File to use as index page (optional, defaults to "README")
    documents: File pattern of documents (optional, defaults to "doc/*")

TODO: Read BLURB file and add additional stuff to index page.
"""

import shutil
from os import path
from glob import glob
from devyco.module import Module


class ProjectModule(Module):

    def _run(self):
        conf = self.read_json('.project.json')
        if conf is None:
            return

        self._get_index(conf)
        self._get_docs(conf)

    def _get_index(self, conf):
        source = path.join(self._target, conf.get('index', 'README'))
        target = path.join(self._target, 'index.adoc')
        shutil.move(source, target)

    def _get_docs(self, conf):
        for doc in glob(path.join(self._target, conf.get('documents', 'doc/*'))):
            target = path.join(self._target, path.basename(doc))
            print "mv %s %s" % (doc, target)
            shutil.move(doc, target)


module = ProjectModule()

if __name__ == '__main__':
    module.test()
