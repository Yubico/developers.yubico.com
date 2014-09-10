"""
Wraps .partial HTML files in a template and outputs full .html files.
"""

import os
from os import path
from jinja2 import Environment, FileSystemLoader
from devyco.module import Module


def display_name(name):
    return name.replace('_', ' ')


def traverse_to(node, remaining):
    if not remaining:
        return node

    next_id = remaining[0]
    remaining = remaining[1:]
    for child in node['children']:
        if child['id'] == next_id:
            return traverse_to(child, remaining)


def set_active(node, remaining):
    if not remaining:
        return

    child_id = remaining[0]
    remaining = remaining[1:]
    for child in node['children']:
        if child['id'] == child_id:
            child['active'] = True
            set_active(child, remaining)
        else:
            child['active'] = False


class PageRenderModule(Module):
    def __init__(self):
        super(PageRenderModule, self).__init__()
        self._site = {'children':[], 'url': None}


    def _run(self):
        if not hasattr(self, '_env'):
            self._env = Environment(
                loader=FileSystemLoader(self._context['basedir']))

        current = self._get_current()
        dirs = filter(path.isdir, self.list_files())
        partials = self.list_files('*.partial')
        htmls = self.list_files('*.html')
        children = dirs + partials + htmls
        self._populate_children(current, children)
        set_active(self._site, self._context['path'])
        self._render_children(current, partials)

    def _get_current(self):
        return traverse_to(self._site, self._context['path'])

    def _populate_children(self, current, children):
        current['children'] = []
        for child in children:
            child_id = path.basename(child).replace('.partial', '.html')
            if child_id == 'index.html':
                continue  # Exclude index pages from being listed
            current['children'].append({
                'id': child_id,
                'url': '/'.join(filter(None, [current['url'], child_id])),
                'name': display_name(child_id.replace('.html', '')),
                'active': False,
                'children': []
            })

    def _render_children(self, current, partials):
        for partial in partials:
            for child in current['children']:
                if path.basename(partial) \
                        .replace('.partial', '.html') == child['id']:
                    child['active'] = True
                    self._render_partial(partial)
                    child['active'] = False
                    break
            else:
                self._render_partial(partial)

    def _render_partial(self, fname):
        out_name = path.basename(fname).replace('.partial', '.html')
        tplt = self._env.get_template('site.template')
        self._context['nav'] = self._site['children']
        with open(fname, 'r') as infile:
            content = infile.read()
        with open(path.join(self._target, out_name), 'w') as outfile:
            outfile.write(tplt.render(content=content, **self._context))
        os.remove(fname)


module = PageRenderModule()

if __name__ == '__main__':
    module.test()
