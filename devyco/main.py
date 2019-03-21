import os
import shutil
import json
import sys
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

    config_file = path.join(target, '.conf.json')
    if path.isfile(config_file):
        with open(config_file, 'r') as f:
            try:
                dirconfig = json.load(f)
            except ValueError:
                sys.stderr.write('Error parsing JSON: %s\n' % config_file)
                raise
    else:
        dirconfig = {}

    context['dirconfig'] = dirconfig
    for module in context['modules']:
        module.run(context)

    excluded = dirconfig.get('exclude', [])

    for item in os.listdir(target):
        abs_item = path.join(target, item)
        if path.isdir(abs_item) and item not in excluded \
                and not item.startswith('.'):
            context['path'].append(item)
            traverse(context)
            context['path'].pop()

    context['dirconfig'] = dirconfig
    for module in context['modules']:
        module.post_run(context)


def copy_static(source, dest):
    # Would prefer to do this in python, but the standard functions are too
    # limited.
    os.system('cp -r %s/* %s/' % (source, dest))


def load_modules(settings, base_dir, dest_dir):
    modules = []
    for name in settings.get('modules', []):
        module = import_module('devyco.modules.%s' % name).module
        conf = settings.get(name, {})
        conf['maindir'] = base_dir
        conf['destdir'] = dest_dir
        module.configure(conf)
        modules.append(module)
    return modules


def main(base_dir=path.curdir, settings=None):
    if settings is None:
        settings = {}

    source = path.join(base_dir, 'content')
    dest = path.join(base_dir, 'htdocs/dist')
    clean(source, dest)

    modules = load_modules(settings, base_dir, dest)

    context = {
        'modules': modules,
        'basedir': dest,
        'path': []
    }

    traverse(context)

    for module in modules:
        module.cleanup(context)

    static = path.join(base_dir, 'static')
    copy_static(static, dest)
