"""
Clones a git repo and extracts data.
"""

import os
import json
import shutil
from os import path
from glob import glob
from devyco.module import Module


class GitModule(Module):

    def _run(self):
        conf_file = path.join(self._target, '.github.json')
        if path.isfile(conf_file):
            with open(conf_file, 'r') as f:
                conf = json.load(f)
            self._extract(conf)

    def _extract(self, conf):
        url = conf['url']
        repo_dir = self.cache_dir(url, False)
        if path.isdir(repo_dir):
            print "Update:", url
            os.system('(cd "%s" && git pull)' % repo_dir)
        else:
            print "clone:", url
            os.system('git clone "%s" "%s"' % (url, repo_dir))
        self._get_index(repo_dir, conf)
        self._get_docs(repo_dir, conf)

    def _get_index(self, repo_dir, conf):
        source = path.join(repo_dir, conf.get('index', 'README'))
        target = path.join(self._target, 'index.adoc')
        shutil.copy(source, target)
        print "cp %s %s" % (source, target)

    def _get_docs(self, repo_dir, conf):
        for doc in glob(path.join(repo_dir, conf.get('documents', 'doc/*'))):
            target = path.join(self._target, path.basename(doc))
            if path.isdir(doc):
                shutil.copytree(doc, target)
            else:
                shutil.copy(doc, target)
            print "cp %s %s" % (doc, target)


module = GitModule()

if __name__ == '__main__':
    module.test()
