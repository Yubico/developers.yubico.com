"""
Generates a releases page based on release artifacts in a directory.
Also generates an atom feed of releases, as atom.xml.
Activated by a "releases" entry in a .conf.json file, containing the following
settings:
    dir: Location of the release artifacts and resulting index page (defaults
    to the current directory).
    abortIfEmpty: True to abort the page creation if there are no releases
    present.

A separate "releases_aggregate_feed" entry in a .conf.json file will create
an aggregate feed containing the latest 50 releases among all projects.
"""

from os import path
from distutils.version import LooseVersion
from devyco.module import Module
import os
import json
import heapq
import time
import re

from feed.atom import Feed, Entry, new_xmldoc_feed, Link, Author

SIG_SUFFIXES = ['sig', 'asc']
SUFFIXES = SIG_SUFFIXES + \
    ['tar', 'gz', 'tgz', 'xz', 'zip', 'exe', 'pkg', 'cap', 'apk', 'msi', 'pdf', 'AppImage']


def classifier(filename):
    # Make sure that the specific classifiers come before the general ones so they are matched first. Tex 'win32' should come before 'win'
    cp = re.compile(r'\b(win32|win64|win|mac-amd64|mac-arm64|mac-universal|mac|linux|amd64)\b')
    m = cp.search(filename)
    if m:
        return m.group()
    else:
        return None

def version(filename):
    vp = re.compile(r"\b\d+\.\d+(\.\d+)?[a-z]?\b")
    version = vp.search(filename).group()
    return version, classifier(filename)

def version_with_classifier(filename):
    vers, classifier = version(filename)
    if classifier:
        return '%s-%s' % (vers, classifier)
    return vers


def extract_versions(files):
    versions = []
    for fname in files:
        v, classifier = version(fname)
        if v not in versions:
            versions.append(v)
    versions.sort(key=LooseVersion, reverse=True)
    return versions


def is_sig(fname):
    for suffix in SIG_SUFFIXES:
        if fname.endswith('.' + suffix):
            return True
    return False


def get_sig(fname, files):
    for suffix in SIG_SUFFIXES:
        sig = '%s.%s' % (fname, suffix)
        if sig in files:
            return sig
    return None


def extract_files(v, files, target):
    matches = []
    for fname in files:
        if version(fname)[0] == v and not is_sig(fname):
            matches.append({
                "filename": fname,
                "sig": get_sig(fname, files),
                "date": get_date(fname, target)
            })
    matches.sort(key=lambda x: LooseVersion(
        version_with_classifier(x['filename'])))
    return matches

def get_date(fname, target):
    date = path.getmtime(path.join(target, fname))
    return time.strftime("%Y-%m-%d", time.gmtime(date))

class ReleasesModule(Module):

    def __init__(self):
        super(ReleasesModule, self).__init__()

        self._all_entries = [(0, None)] * 50  # Max items in aggregate feed

    def _run(self):
        if os.environ.get('NORELEASES'):
            return

        conf = self.get_conf('releases')
        if conf is None:
            return

        target = conf.get('dir', '.')

        all_files = map(path.basename, self.list_files(relative=target))
        if not all_files and conf.get('abortIfEmpty', False):
            return

        versions = extract_versions(all_files)

        entries = []
        for v in versions:
            entries.append({
                "version": v,
                "files": extract_files(v, all_files, path.join(self._target, target))
            })

        tplt = self.get_template('releases')

        outpath = path.join(self._target, target, 'index.partial')
        if not path.isdir(path.dirname(outpath)):
            os.makedirs(path.dirname(outpath))
        with open(outpath, 'w') as outfile:
            outfile.write(tplt.render(releases=entries).encode('utf-8'))

        self.create_feed(entries, path.dirname(outpath), target)

        # Add feed link to main page.
        mainvars = self.get_conf('vars', [])
        mainvars.append({'filter': 'index', 'values': {'release_feed': target + '/atom.xml'}})

        # Add feed link to releases page.
        confpath = path.join(self._target, target, '.conf.json')
        if not path.isfile(confpath):
            conf = {}
        else:
            with open(confpath, 'r') as f:
                conf = json.load(f)

        variables = conf.setdefault('vars', [])
        variables.append({'filter': 'index', 'values': {'release_feed': 'atom.xml'}})

        with open(confpath, 'w') as f:
            json.dump(conf, f)

        redirects = self._create_latest(entries, path.join(self._context['path'][0], target), target)

        if redirects:
            htaccess = path.join(self._target, '.htaccess')
            with open(htaccess, 'a') as f:
                f.writelines(redirects)

    def _create_latest(self, entries, path, relpath):
        ret = 'RewriteEngine On\n'
        created = {}
        for entry in entries:
            ver = entry["version"]
            for f in entry["files"]:
                name = f["filename"]
                sig = f["sig"]
                match = re.search(r"-" + ver + "(.+)$", name)
                if match:
                    suffix = match.group(1)
                    if suffix in created:
                        continue
                    created[suffix] = 1
                    link = re.sub(r"-" + ver, "-latest", name)
                    redir = 'RewriteRule ^%s/%s$ %%{ENV:REQUEST_PROTO}://%%{HTTP_HOST}/%s/%s [L,R=302]\n' % (
                            relpath, link, path, name)
                    ret += redir
                    if sig:
                        link = re.sub(r"-" + ver, "-latest", sig)
                        redir = 'RewriteRule ^%s/%s$ %%{ENV:REQUEST_PROTO}://%%{HTTP_HOST}/%s/%s [L,R=302]\n' % (
                                relpath, link, path, sig)
                        ret += redir
        return ret

    def _post_run(self):
        if os.environ.get('NORELEASES'):
            return
        aggregate = self.get_conf('releases_aggregate_feed')
        if not aggregate or not self._all_entries:
            return

        xmldoc, feed = new_xmldoc_feed()
        feed.id = "https://developers.yubico.com/Software_Projects/"
        feed.title = "Yubico software releases"
        link = Link("https://developers.yubico.com/" + aggregate)
        link.attrs["rel"] = "self"
        feed.links.append(link)
        entries = sorted(self._all_entries, reverse=True)
        feed.updated = entries[0][0]
        for (t, e) in entries:
            feed.entries.append(e)
            if e is None:
                break

        outpath = path.join(self._target, aggregate)
        if not path.isdir(path.dirname(outpath)):
            os.makedirs(path.dirname(outpath))
        with open(outpath, 'w') as outfile:
            outfile.write(str(xmldoc))

    def create_feed(self, entries, outdir, target):
        name = self._context['path'][0]
        xmldoc, feed = new_xmldoc_feed()
        feed.id = "https://developers.yubico.com/%s/Releases/" % (name)
        feed.title = name + " Releases"
        link = Link("https://developers.yubico.com/%s/Releases/atom.xml" % (name))
        link.attrs["rel"] = "self"
        feed.links.append(link)
        mtimes = []
        for entry in entries:
            for file in entry['files']:
                e = Entry()
                e.id = "https://developers.yubico.com/%s/Releases/%s" % (name, file['filename'])
                e.title = file['filename']
                e.author = Author("Yubico")
                e.updated = path.getmtime(path.join(self._target, target, file['filename']))
                mtimes.append(e.updated)
                e.summary = "Release %s of %s" % (entry['version'], name)
                link = Link("https://developers.yubico.com/%s/Releases/%s" % (name, file['filename']))
                e.links.append(link)
                feed.entries.append(e)

                if self._all_entries[0][0] < e.updated:
                    heapq.heapreplace(self._all_entries, (e.updated, e))

        feed.updated = max(mtimes)

        with open(outdir + "/atom.xml", 'w') as outfile:
            outfile.write(str(xmldoc))

module = ReleasesModule()

if __name__ == '__main__':
    module.test()
