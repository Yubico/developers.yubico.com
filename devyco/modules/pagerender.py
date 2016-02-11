"""
Wraps .partial HTML files in a template and outputs full .html files.
Files listed in a "hidden" entry of the .conf.json will not be shown in the
navigation.
Entries in the "links" entry of the .conf.json will be shown on the page.
"""

from os import path
from fnmatch import fnmatch
from bs4 import BeautifulSoup
from devyco.module import Module, noext, merge_data
import os
import re


EXTERNAL_LINK = re.compile(r'^(https?:)?//(?!developers\.yubico\.com)')


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
        for child in node['children']:
            child['active'] = False
        return node

    child_id = remaining[0]
    remaining = remaining[1:]
    active_child = None

    for child in node['children']:
        if child['id'] == child_id:
            child['active'] = True
            active_child = set_active(child, remaining)
        else:
            child['active'] = False
    return active_child


class PageRenderModule(Module):
    def __init__(self):
        super(PageRenderModule, self).__init__()
        self._site = {'id': '', 'children': [], 'url': ''}

    def _run(self):
        current = self._get_current()
        documents = self.list_files(['*.partial', '*.html'])
        children = self.list_files(['*.partial', '*.html'], include_dirs=True)
        self._populate_children(current, children)
        self._context['nav'] = self._site['children']
        self._render_children(current, filter(lambda x: x.endswith('.partial'),
                                              documents))

    def _post_run(self):
        self._get_current()
        documents = self.list_files(['*.partial', '*.html'])
        self._ensure_index(documents)

    def _get_current(self):
        return set_active(self._site, self._context['path'])

    def _populate_children(self, current, children):
        hidden = map(noext, self.get_conf('hidden', []))
        current['children'] = []
        for child in children:
            child_id = path.basename(child).replace('.partial', '.html')
            if child_id == 'index.html':
                continue  # Exclude index pages from being listed
            child_name = child_id.replace('.html', '')
            hide = child_name in hidden or path.isdir(child) \
                and not os.listdir(child)
            current['children'].append({
                'id': child_id,
                'url': current['url'] + '/' + child_id,
                'name': display_name(child_name),
                'active': False,
                'hidden': hide,
                'children': []
            })

    def _render_children(self, current, partials):
        self._context['current'] = current['id']
        for partial in partials:
            for child in current['children']:
                if path.basename(partial) \
                        .replace('.partial', '.html') == child['id']:
                    child['active'] = True
                    self._context['current'] = child['id']
                    self._context['title'] = child['name']
                    self._render_partial(partial)
                    child['active'] = False
                    break
            else:
                self._context['current'] = current['id']
                self._context['title'] = display_name(current['id'])
                self._render_partial(partial)

    def _get_vars(self, basename, values):
        for entry in self.get_conf('vars', []):
            if fnmatch(basename, entry.get('filter', '*')):
                merge_data(values, entry.get('values'))

    def _render_partial(self, fname):
        basename = path.basename(fname).replace('.partial', '')
        out_name = basename + '.html'
        tpltvars = dict(self._context)
        self._get_vars(basename, tpltvars)
        tplt = self.get_template('site')
        with open(fname, 'r') as infile:
            content = infile.read().decode('utf-8')
        rendered = tplt.render(content=content, **tpltvars)
        rendered = self._post_process(rendered, basename)
        with open(path.join(self._target, out_name), 'w') as outfile:
            outfile.write(rendered.encode('utf-8'))
        os.remove(fname)

    def _post_process(self, content, basename):
        soup = BeautifulSoup(content)
        content = soup.body.find(id='page-content')
        elem = content.find(lambda x: x.string)
        while elem and elem.name not in ['h1', 'h2']:
            if elem == content:
                title = self._context.get('title') or \
                    display_name(self._context['current'])
                content.insert(0, BeautifulSoup('<h2>%s</h2>' % title))
                break
            elem = elem.parent

        for link in soup.find_all('a', href=EXTERNAL_LINK):
            link['target'] = '_blank'

        return soup

    def _ensure_index(self, documents):
        index_partial = path.join(self._target, 'index.partial')
        index_html = path.join(self._target, 'index.html')
        if index_partial not in documents and index_html not in documents:
            self._context['title'] = display_name(self._context['path'][-1])
            documents.append(index_partial)
            tplt = self.get_template('index')
            with open(index_partial, 'w') as f:
                f.write(tplt.render(**self._context).encode('utf-8'))
            self._render_partial(index_partial)


module = PageRenderModule()

if __name__ == '__main__':
    module.test()
