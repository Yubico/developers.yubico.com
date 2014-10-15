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
from os import path
from glob import glob
from devyco.module import Module


class GitModule(Module):

    def __init__(self):
        super(GitModule, self).__init__()
        self._updated = []

    def _run(self):
        confs = self.get_conf('git')
        if confs is None:
            return

        if not isinstance(confs, list):
            confs = [confs]

        for conf in confs:
            repo_dir = self._clone(conf)
            self._copy_files(repo_dir, conf.get('files', '*'))

    def _clone(self, conf):
        url = conf['url']
        repo_dir = self.cache_dir(url, False)

        if url not in self._updated:
            if path.isdir(repo_dir):
                if os.environ.get('NOGIT'):
                    print "NOGIT set, skip update"
                    return repo_dir
                print "Update:", url
                os.system('(cd "%s" && git pull 2>&1)' % repo_dir)
            else:
                print "clone:", url
                os.system('git clone "%s" "%s" 2>&1' % (url, repo_dir))
            self._updated.append(url)
        else:
            print "Already updated:", url
        return repo_dir

    def _copy_files(self, repo_dir, files):
        if isinstance(files, basestring):
            files = [files]
        for fpattern in files:
            if isinstance(fpattern, basestring):
                self._copy_file(repo_dir, fpattern, None)
            else:
                fpattern, dest = fpattern
                self._copy_file(repo_dir, fpattern, dest)

    def _copy_file(self, repo_dir, fpattern, dest=None):
        for match in glob(path.join(repo_dir, fpattern)):
            if dest is None:
                target = path.join(self._target, match[len(repo_dir)+1:])
                dest_dir = path.dirname(target)
            else:
                target = path.join(self._target, dest)
                dest_dir = target
            if not path.isdir(dest_dir):
                os.makedirs(dest_dir)
            if path.isdir(match):
                shutil.copytree(match, target)
            else:
                shutil.copy(match, target)


module = GitModule()

if __name__ == '__main__':
    module.test()
