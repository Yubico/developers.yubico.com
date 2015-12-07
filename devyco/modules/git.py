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
                os.system('(cd "%s" && git fetch 2>&1 && git reset origin/master --hard)' % repo_dir)
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
                dest_dir = path.dirname(target)
            if not path.isdir(dest_dir):
                os.makedirs(dest_dir)
            if path.isdir(match):
                shutil.copytree(match, path.join(target, path.basename(match)))
            else:
                shutil.copy(match, target)

    def _create_redirects(self, repo_dir, entries):
        redirects = []
        if isinstance(entries, basestring):
            entries = [entries]
        for entry in entries:
            directory = entry.get('dir', '')
            prefix = path.join(repo_dir, directory)
            for fpattern in entry.get('files', ['*']):
                for match in glob(path.join(prefix, fpattern)):
                    match = match[len(prefix)+1:]
                    names = self._get_old_names(repo_dir, directory, match)
                    names = self._substitutions(names, entry.get('sub'))
                    redirects += self._redirects_for(names)
        if redirects:
            print "\n\n\n\n!!!!!!!!REDIRECTS:", redirects
            htaccess = path.join(self._target, '.htaccess')
            print "DEST:", htaccess
            with open(htaccess, 'w') as f:
                f.writelines(redirects)
            print "\n\n\n\n"

    def _get_old_names(self, repo_dir, directory, fname):
        p = subprocess.Popen(['git', 'log', '--name-only', '--oneline', '--follow', fname],
                             stdout=subprocess.PIPE,
                             cwd=path.join(repo_dir, directory))
        (out, err) = p.communicate()

        prefix = path.join(directory, '')
        lines = [line[len(prefix):] for line in out.splitlines()
                 if line.startswith(directory)]
        seen = set()
        lines = [x for x in lines if x not in seen and not seen.add(x)]
        return filter(None, lines)

    def _substitutions(self, names, subs):
        if isinstance(subs, basestring):
            subs = [subs]
        for sub in subs:
            names = [re.sub(sub['pattern'], sub['repl'], name) for name in names]
        return names

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
