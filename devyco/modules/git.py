"""
Clones a git repo and extracts data.
Activated by a "git" entry in .conf.json, containing the following settings:
    url: Git repository URL (required).
    files: List of filepatterns to copy from the repository (default: all)

The "git" entry can also be a list of objects containing the settings above if
multiple repositories should be clones.
"""

import os
import re
import sys
import shutil
import subprocess
from os import path
from glob import glob
from devyco.module import Module


class GitModule(Module):

    def __init__(self):
        super(GitModule, self).__init__()
        self._updated = []

    def _run(self):
        if os.environ.get('NOPROJECTS'):
            self._context['dirconfig']['git'] = None

        confs = self.get_conf('git')
        if confs is None:
            return

        if not isinstance(confs, list):
            confs = [confs]

        for conf in confs:
            repo_dir = self._clone(conf)
            self._copy_files(repo_dir, conf.get('files', '*'))
            self._create_redirects(repo_dir, conf.get('redirect_renamed', []))

    def _clone(self, conf):
        url = conf['url']
        repo_dir = self.cache_dir(url, False)

        if url not in self._updated:
            if path.isdir(repo_dir):
                if os.environ.get('OFFLINE'):
                    print "OFFLINE set, skip update"
                    return repo_dir
                print "Update:", url
                subprocess.call(['git', 'fetch'], cwd=repo_dir,
                                stderr=sys.stdout.fileno())
                subprocess.call(['git', 'reset', 'origin/master', '--hard'],
                                cwd=repo_dir, stderr=sys.stdout.fileno())
            else:
                print "clone:", url
                subprocess.call(['git', 'clone', url, repo_dir],
                                stderr=sys.stdout.fileno())

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
                dest_dir = path.dirname(target)
            if not path.isdir(dest_dir):
                os.makedirs(dest_dir)
            if path.isdir(match):
                shutil.copytree(match, path.join(target, path.basename(match)))
            else:
                shutil.copy2(match, target)

    def _create_redirects(self, repo_dir, entries):
        redirects = []
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            subs = entry.get('sub', [])
            if not isinstance(subs, list):
                subs = [subs]
            directory = entry.get('dir', '')
            prefix = path.join(repo_dir, directory)
            for fpattern in entry.get('files', ['*']):
                for match in glob(path.join(prefix, fpattern)):
                    match = match[len(prefix)+1:]
                    names = self._get_old_names(repo_dir, directory, match, subs)
                    redirects += self._redirects_for(names)
        if redirects:
            htaccess = path.join(self._target, '.htaccess')
            with open(htaccess, 'w') as f:
                f.writelines(redirects)

    def _get_old_names(self, repo_dir, directory, fname, subs):
        p = subprocess.Popen(['git', 'log', '--name-only', '--oneline', '--follow', fname],
                             stdout=subprocess.PIPE,
                             cwd=path.join(repo_dir, directory))
        (out, err) = p.communicate()

        prefix = path.join(directory, '')
        lines = [line[len(prefix):] for line in out.splitlines()
                 if line.startswith(directory)]
        seen = set()
        uniques = []
        for line in [l for l in lines if l]:
            for sub in subs:
                line = re.sub(sub['pattern'], sub['repl'], line)
            if line not in seen:
                seen.add(line)
                uniques.append(line)
        return uniques

    def _redirects_for(self, names):
        if len(names) < 2:
            return []

        redirects = set()
        basepath = path.join(*self._context['path'])
        new_path = path.join(basepath, names[0])
        for old_name in names[1:]:
            redirects.add('Redirect 301 "/%s" "/%s"\n' % (
                path.join(basepath, old_name), new_path))
        return list(redirects)


module = GitModule()

if __name__ == '__main__':
    module.test()
