"""
Converts AsciiDoc formatted files with .adoc extension to .partial HTML files.
"""

import sys
import os
from devyco.module import Module, noext

sys.path.append('/usr/share/asciidoc/')
from asciidocapi import AsciiDocAPI, AsciiDocError


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
            try:
                self._asciidoc.execute(item, noext(item) + '.partial')
                for message in self._asciidoc.messages:
                    sys.stderr.write('Error parsing Asciidoc file %s: %s\n' % (item, message))
                self.processed_files.append(item)
            except AsciiDocError as e:
                sys.stderr.write("Error parsing AsciiDoc in file: %s\n" % item)
                sys.stderr.write("%s\n" % e.message)

    def cleanup(self, context):
        for f in self.processed_files:
            os.remove(f)

module = AsciiDocModule()

if __name__ == '__main__':
    module.test()
