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

from feed.atom import Feed, Entry, new_xmldoc_feed, Link, Author

SIG_SUFFIXES = ['sig', 'asc']
SUFFIXES = SIG_SUFFIXES + \
    ['tar', 'gz', 'tgz', 'xz', 'zip', 'exe', 'pkg', 'cap', 'apk', 'msi', 'pdf']
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
    return version, classifier


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


def extract_files(v, files):
    matches = []
    for fname in files:
        if version(fname)[0] == v and not is_sig(fname):
            matches.append({
                "filename": fname,
                "sig": get_sig(fname, files)
            })
    matches.sort(key=lambda x: LooseVersion(
        version_with_classifier(x['filename'])))
    return matches


class ReleasesModule(Module):

    def __init__(self):
        super(ReleasesModule, self).__init__()

        self._all_entries = [(0, None)] * 50  # Max items in aggregate feed

    def _run(self):
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
                "files": extract_files(v, all_files)
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

    def _post_run(self):
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
