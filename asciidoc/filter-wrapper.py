#!  /usr/bin/env python
"""Simple wrapper for filter programs which ensures that a blank
is returned as output.  The purpose is to silence the
AsciiDoc warning "no output from filter".
"""


import sys, subprocess

p = subprocess.Popen(sys.argv[1:])
sys.stdout.write(' ') # To suppress asciidoc 'no output from filter' warnings.
sys.exit(p.wait())

