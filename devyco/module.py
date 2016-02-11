import os
from os import path
from glob import glob
from hashlib import sha1
from jinja2 import Environment, FileSystemLoader


def hash(value):
    f = sha1()
    f.update(value)
    return f.hexdigest()


def noext(fname):
    if '.' in fname:
        return fname.rsplit('.', 1)[0]
    return fname


def merge_data(base, added):
    for (key, value) in added.items():
        if key not in base:
            base[key] = value
        else:
            base_value = base[key]
            if isinstance(value, dict):
                if not isinstance(base_value, dict):
                    raise ValueError('Cannot merge data: %r with %r' %
                                     (value, base_value))
                merge_data(base_value, value)
            elif isinstance(value, list):
                if isinstance(base_value, list):
                    base_value.extend(value)
                else:
                    base[key] = [base_value] + value
            else:  # Can't merge, just overwrite
                base[key] = value


class Module(object):

    """
    Abstract base class for modules.
    """

    def __init__(self):
        self._conf = {}

    def configure(self, conf):
        self._conf.update(conf)
        cachedir = path.join(conf['maindir'], '.cache')
        self._conf['cachedir'] = cachedir
        if not path.isdir(cachedir):
            os.mkdir(cachedir)
        self._conf['templatedir'] = path.join(conf['maindir'], 'templates')
        self._configure()

    def _configure(self):
        pass

    def run(self, context):
        self._context = context
        self._target = path.join(context['basedir'], *context['path'])
        self._run()

    def post_run(self, context):
        self._context = context
        self._target = path.join(context['basedir'], *context['path'])
        self._post_run()

    def _run(self):
        raise NotImplementedError('Subclasses must implement this!')

    def _post_run(self):
        pass

    def cleanup(self, context):
        pass

    def get_conf(self, name, default=None):
        return self._context['dirconfig'].setdefault(name, default)

    def get_template(self, name):
        env = Environment(loader=FileSystemLoader(self._conf['templatedir']))
        return env.get_template('%s.template' % name)

    def list_dirs(self, target):
        return filter(os.path.isdir, glob(path.join(target, '*')))

    def list_files(self, name_filters='*', relative='', include_dirs=False):
        target = path.join(self._target, relative)
        if not isinstance(name_filters, list):
            name_filters = [name_filters]
        target_files = []
        for name_filter in name_filters:
            target_files.extend(glob(path.join(target, name_filter)))
        if include_dirs:
            target_files.extend(self.list_dirs(target))
        return self._sort(target, self._exclude(target, target_files))

    def read_files_list(self, basedir, fname):
        fpath = path.join(basedir, fname)
        if path.isfile(fpath):
            with open(fpath, 'r') as f:
                return map(noext, f.read().splitlines())
        return []

    def _exclude(self, basedir, files):
        target_files = []
        exclude = map(noext, self.get_conf('exclude', []))
        for filename in files:
            if noext(path.basename(filename)) not in exclude:
                target_files.append(filename)
        return target_files

    def _sort(self, basedir, files):
        sorted_files = []
        target_files = files[:]
        for name in map(noext, self.get_conf('order', [])):
            for filename in target_files[:]:
                if noext(path.basename(filename)) == name:
                    sorted_files.append(filename)
                    target_files.remove(filename)
                    break
        target_files.sort()
        sorted_files.extend(target_files)
        return sorted_files

    def cache_dir(self, key, create=True):
        digest = hash('%s:%s' % (self.__module__, key))
        target = path.join(self._conf['cachedir'], digest)
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
