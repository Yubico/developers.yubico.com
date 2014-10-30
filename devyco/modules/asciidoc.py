"""
Converts AsciiDoc formatted files with .adoc extension to .partial HTML files.
"""

import sys
import os
import re
from devyco.module import Module, noext
from bs4 import BeautifulSoup

sys.path.append('/usr/share/asciidoc/')
from asciidocapi import AsciiDocAPI, AsciiDocError


ADOC_LINK = re.compile(r'\.a(scii)?doc$')


class AsciiDocModule(Module):

    def _configure(self):
        self._asciidoc = AsciiDocAPI()
        self._asciidoc.attributes['root'] = self._conf['destdir']
        conf_file = os.path.join(self._conf['maindir'], 'asciidoc-devyco.conf')
        self._asciidoc.options('--conf-file', conf_file)
        self._asciidoc.options('--no-header-footer')
        self.processed_files = []

    def _run(self):
        for item in self.list_files(['*.adoc', '*.asciidoc', '*.txt']):
            target = noext(item) + '.partial'
            self._convert(item, target)
            self._post_process(target)

    def _convert(self, source, target):
        try:
            self._asciidoc.execute(source, target)
            for message in self._asciidoc.messages:
                sys.stderr.write('Error parsing Asciidoc file %s: %s\n' %
                                 (source, message))
            self.processed_files.append(source)
        except AsciiDocError as e:
            sys.stderr.write("Error parsing AsciiDoc in file: %s\n" % source)
            sys.stderr.write("%s\n" % e.message)

    def _post_process(self, target):
        soup = BeautifulSoup(open(target, 'r'))
        for link in soup.find_all('a', href=ADOC_LINK):
            link['href'] = noext(link['href']) + '.html'

        with open(target, 'w') as f:
            f.write(soup.prettify().encode('utf-8'))

    def cleanup(self, context):
        for f in self.processed_files:
            os.remove(f)

module = AsciiDocModule()

if __name__ == '__main__':
    module.test()
