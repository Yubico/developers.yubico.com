import os
import json
from os import path
from glob import glob
from hashlib import sha1


def hash(value):
    f = sha1()
    f.update(value)
    return f.hexdigest()


def noext(fname):
    if '.' in fname:
        return fname.rsplit('.', 1)[0]
    return fname


class Module(object):

    """
    Abstract base class for modules.
    """

    def __init__(self):
        self._conf = {}

    def configure(self, conf):
        self._conf.update(conf)

    def run(self, context):
        self._context = context
        self._target = path.join(context['basedir'], *context['path'])
        self._run()

    def _run(self):
        raise NotImplementedError('Subclasses must implement this!')

    def list_files(self, name_filters='*', relative=''):
        target = path.join(self._target, relative)
        if not isinstance(name_filters, list):
            name_filters = [name_filters]
        target_files = []
        for name_filter in name_filters:
            target_files.extend(glob(path.join(target, name_filter)))
        return self._sort(target, self._exclude(target, target_files))

    def read_files_list(self, basedir, fname):
        fpath = path.join(basedir, fname)
        if path.isfile(fpath):
            with open(fpath, 'r') as f:
                return map(noext, f.read().splitlines())
        return []

    def _exclude(self, basedir, files):
        target_files = []
        exclude = map(noext, self._context['dirconfig'].get('exclude', []))
        for filename in files:
            if noext(path.basename(filename)) not in exclude:
                target_files.append(filename)
        return target_files

    def _sort(self, basedir, files):
        sorted_files = []
        target_files = files[:]
        for name in map(noext, self._context['dirconfig'].get('order', [])):
            for filename in target_files[:]:
                if noext(path.basename(filename)) == name:
                    sorted_files.append(filename)
                    target_files.remove(filename)
                    break
        target_files.sort()
        sorted_files.extend(target_files)
        return sorted_files

    def cache_dir(self, key, create=True):
        digest = hash(':'.join(self._context['path'] + [key]))
        target = path.join(self._context['cachedir'], digest)
        if not path.isdir(target) and create:
            os.mkdir(target)
        return target

    def test(self):
        source = path.abspath(path.curdir)
        dest = path.join(source, '.test')
        from devyco.main import clean
        clean(source, dest)

        self.run({
            'modules': [self],
            'basedir': dest,
            'path': []
        })
