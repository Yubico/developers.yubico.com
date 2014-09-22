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
        self._site = {'children': [], 'url': ''}

    def _run(self):
        if not hasattr(self, '_env'):
            self._env = Environment(
                loader=FileSystemLoader(self._context['basedir']))

        current = self._get_current()
        dirs = filter(path.isdir, self.list_files())
        documents = self.list_files(['*.partial', '*.html'])
        children = dirs + documents
        self._populate_children(current, children)
        set_active(self._site, self._context['path'])
        self._context['nav'] = self._site['children']
        self._render_children(current, filter(lambda x: x.endswith('.partial'),
                                              documents))
        self._ensure_index()

    def _get_current(self):
        return traverse_to(self._site, self._context['path'])

    def _populate_children(self, current, children):
        hidden = self.read_files_list(self._target, '.hidden')
        current['children'] = []
        for child in children:
            child_id = path.basename(child).replace('.partial', '.html')
            if child_id == 'index.html':
                continue  # Exclude index pages from being listed
            child_name = child_id.replace('.html', '')
            current['children'].append({
                'id': child_id,
                'url': current['url'] + '/' + child_id,
                'name': display_name(child_name),
                'active': False,
                'hidden': child_name in hidden,
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
        with open(fname, 'r') as infile:
            content = infile.read().decode('utf-8')
        with open(path.join(self._target, out_name), 'w') as outfile:
            outfile.write(tplt.render(content=content, **self._context) \
                          .encode('utf-8'))
        os.remove(fname)

    def _ensure_index(self):
        index_file = path.join(self._target, 'index.html')
        if not path.isfile(index_file):
            tplt = self._env.get_template('site.template')
            with open(index_file, 'w') as f:
                f.write(tplt.render(content=u'', **self._context) \
                        .encode('utf-8'))


module = PageRenderModule()

if __name__ == '__main__':
    module.test()
