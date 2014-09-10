import os
from os import path
from glob import glob
from hashlib import sha1


def hash(value):
    f = sha1()
    f.update(value)
    return f.hexdigest()


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

    def list_files(self, name_filter='*', relative=''):
        target = path.join(self._target, relative)
        target_files = glob(path.join(target, name_filter))
        return map(lambda x: path.join(target, x), target_files)

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
