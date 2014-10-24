"""
Converts AsciiDoc formatted files with .adoc extension to .partial HTML files.
"""

import sys
import os
from devyco.module import Module, noext

sys.path.append('/usr/share/asciidoc/')
from asciidocapi import AsciiDocAPI, AsciiDocError


class AsciiDocModule(Module):
    def __init__(self):
        super(AsciiDocModule, self).__init__()
        self._asciidoc = AsciiDocAPI()
        self._asciidoc.options('--no-header-footer')
        self.processed_files = []

    def _run(self):
        for item in self.list_files(['*.adoc', '*.asciidoc', '*.txt']):
            try:
                self._asciidoc.attributes['root'] = self._context['basedir']
                self._asciidoc.execute(item, noext(item) + '.partial', backend='html5')
                for message in self._asciidoc.messages:
                    sys.stderr.write('Error parsing Asciidoc file %s: %s\n' % (item, message))
                self.processed_files.append(item)
            except AsciiDocError:
                sys.stderr.write("Error parsing AsciiDoc in file: %s\n" % item)

    def cleanup(self, context):
        for f in self.processed_files:
            os.remove(f)

module = AsciiDocModule()

if __name__ == '__main__':
    module.test()
