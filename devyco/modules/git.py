"""
Clones a git repo and extracts data.
Activated by a "git" entry in .conf.json, containing the following settings:
    url: Git repository URL (required).
    files: List of filepatterns to copy from the repository (default: all)
    preserve_mtimes: If true, set mtimes based on commit times (default: false)

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


def _try_startswith(line, prefix):
    try:
        return line.startswith(prefix)
    except:
        return False


class GitModule(Module):

    def __init__(self):
        super(GitModule, self).__init__()
        self._updated = []
        if os.environ.get('NORELEASES'):
            self._updated.append('git@github.com:Yubico/yubico-binaries.git')

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
            self._more_redirects(repo_dir, conf.get('redirects', []))

    def _fix_mtimes(self, repo_dir):
        print "Preserving mtimes for:", repo_dir
        proc = subprocess.Popen(['git', 'log', '--pretty=%at', '--name-status'],
                                cwd=repo_dir, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        mtime = 0
        added = set([''])
        for line in stdout.splitlines():
            try:
                mtime = int(line)
            except:
                if line not in added and line[0] in ['A', 'M']:
                    added.add(line)
                    fname = os.path.join(repo_dir, line[2:])
                    if os.path.isfile(fname):
                        os.utime(fname, (mtime, mtime))

    def _clone(self, conf):
        url = conf['url']
        repo_dir = self.cache_dir(url, False)

        if url not in self._updated:
            if path.isdir(repo_dir):
                if os.environ.get('OFFLINE'):
                    print "OFFLINE set, skip update"
                    return repo_dir
                print "Update:", url
                subprocess.check_call(['git', 'fetch', 'origin', 'master'],
                                      cwd=repo_dir, stderr=sys.stdout.fileno())
                subprocess.check_call(['git', 'reset', 'origin/master', '--hard'],
                                      cwd=repo_dir, stderr=sys.stdout.fileno())
            else:
                print "clone:", url
                subprocess.check_call(['git', 'clone', url, repo_dir],
                                stderr=sys.stdout.fileno())

            if conf.get('preserve_mtimes'):
                self._fix_mtimes(repo_dir)

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

    def _more_redirects(self, repo_dir, entries):
        redirects = []
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            redirects += self._redirects_for(entry)
        if redirects:
            htaccess = path.join(self._target, '.htaccess')
            with open(htaccess, 'a') as f:
                f.writelines(redirects)

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
            with open(htaccess, 'a') as f:
                f.writelines(["RewriteEngine On\n"])
                f.writelines(redirects)

    def _get_old_names(self, repo_dir, directory, fname, subs):
        p = subprocess.Popen(['git', 'log', '--name-only', '--oneline', '--follow', fname],
                             stdout=subprocess.PIPE,
                             cwd=path.join(repo_dir, directory))
        (out, err) = p.communicate()

        prefix = path.join(directory, '')
        lines = [line[len(prefix):] for line in out.splitlines()
                 if _try_startswith(line, directory)]
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
            redirects.add('RewriteRule ^%s$ %%{ENV:REQUEST_PROTO}://%%{HTTP_HOST}/%s [L,R=301]\n' % (
                old_name, new_path))
        return list(redirects)


module = GitModule()

if __name__ == '__main__':
    module.test()
