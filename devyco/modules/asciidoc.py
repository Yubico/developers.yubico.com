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

    def _run(self):
        for item in self.list_files(['*.adoc', '*.asciidoc', '*.txt']):
            try:
                self._asciidoc.execute(item, noext(item) + '.partial')
                os.remove(item)
            except AsciiDocError:
                sys.stderr.write("Error parsing AsciiDoc in file: %s\n" % item)


module = AsciiDocModule()

if __name__ == '__main__':
    module.test()
