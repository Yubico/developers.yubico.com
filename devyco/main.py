import os
import shutil
from os import path
from importlib import import_module


def clean(source, dest):
    if path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def traverse(context):
    target = path.join(context['basedir'], *context['path'])
    if not path.isdir(target):
        os.mkdir(target)

    for module in context['modules']:
        module.run(context)

    exclude_file = path.join(target, '.exclude')
    excluded = []
    if path.isfile(exclude_file):
        with open(exclude_file, 'r') as f:
            excluded = f.read().splitlines()

    for item in os.listdir(target):
        abs_item = path.join(target, item)
        if path.isdir(abs_item) and item not in excluded \
                and not item.startswith('.'):
            context['path'].append(item)
            traverse(context)
            context['path'].pop()


def copy_static(source, dest):
    # Would prefer to do this in python, but the standard functions are too
    # limited.
    os.system('cp -r %s/* %s/' % (source, dest))


def load_modules(settings):
    modules = []
    for name in settings.get('modules', []):
        module = import_module('devyco.modules.%s' % name).module
        module.configure(settings.get(name, {}))
        modules.append(module)
    return modules


def main(base_dir=path.curdir, settings=None):
    if settings is None:
        settings = {}

    modules = load_modules(settings)

    source = path.join(base_dir, 'content')
    dest = path.join(base_dir, 'dist')
    clean(source, dest)
    cache = path.join(base_dir, '.cache')
    if not path.isdir(cache):
        os.mkdir(cache)

    context = {
        'modules': modules,
        'basedir': dest,
        'cachedir': cache,
        'path': []
    }

    traverse(context)

    static = path.join(base_dir, 'static')
    copy_static(static, dest)
