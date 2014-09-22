"""
Clones a git repo and extracts data.
Activated by a .git.json file in a content directory, containing the following
settings:
    url: Git repository URL (required).
    files: List of filepatterns to copy from the repository (default: all)
"""

import os
import shutil
from os import path
from glob import glob
from devyco.module import Module


class GitModule(Module):

    def _run(self):
        conf = self.read_json('.git.json')
        if conf is None:
            return

        repo_dir = self._clone(conf)
        self._copy_files(repo_dir, conf.get('files', '*'))

    def _clone(self, conf):
        url = conf['url']
        repo_dir = self.cache_dir(url, False)
        if path.isdir(repo_dir):
            print "Update:", url
            os.system('(cd "%s" && git pull)' % repo_dir)
        else:
            print "clone:", url
            os.system('git clone "%s" "%s"' % (url, repo_dir))
        return repo_dir

    def _copy_files(self, repo_dir, files):
        if isinstance(files, basestring):
            files = [files]
        for fpattern in files:
            if isinstance(fpattern, basestring):
                self._copy_file(repo_dir, fpattern, self._target)
            else:
                fpattern, dest = fpattern
                self._copy_file(repo_dir, fpattern, dest)

    def _copy_file(self, repo_dir, fpattern, dest):
        for match in glob(path.join(repo_dir, fpattern)):
            target = path.join(dest, match[len(repo_dir)+1:])
            dest_dir = path.dirname(target)
            if not path.isdir(dest_dir):
                os.makedirs(dest_dir)
            print "copy to", target
            if path.isdir(match):
                shutil.copytree(match, target)
            else:
                shutil.copy(match, target)

    def _get_index(self, repo_dir, conf):
        source = path.join(repo_dir, conf.get('index', 'README'))
        target = path.join(self._target, 'index.adoc')
        shutil.copy(source, target)

    def _get_docs(self, repo_dir, conf):
        for doc in glob(path.join(repo_dir, conf.get('documents', 'doc/*'))):
            target = path.join(self._target, path.basename(doc))
            if path.isdir(doc):
                shutil.copytree(doc, target)
            else:
                shutil.copy(doc, target)


module = GitModule()

if __name__ == '__main__':
    module.test()
