"""
Adds a 'Suggest Edits' link to pages.
"""

import re
import urllib
from devyco.module import Module, noext
from os import path

CREATE_GITHUB_ISSUE_URL = 'https://github.com/Yubico/developers.yubico.com/issues/new?title=Suggested%20edit%20for%20{filename}&body=(Write%20your%20suggestions%20here)%0A%0A---%0ASee%20https://developers.yubico.com/{urlname}'


class SuggestedEditsModule(Module):
    def __init__(self):
        super(SuggestedEditsModule, self).__init__()

    def _run(self):
        suggest_edits = self.get_conf('suggest-edits')
        if suggest_edits is not None:
            variables = self.get_conf('vars', [])
            self._add_suggest_edits_link(variables)

    def _add_suggest_edits_link(self, variables):
        for f in self.list_files('*.partial'):
            basename = noext(path.basename(f))
            filename = path.join(*(self._context['path'] + [basename]))
            urlname = re.sub("/index$", "/", filename)

            variables.append({
                'filter': basename,
                'values': {
                    'sidelinks': [
                        {
                            'url': CREATE_GITHUB_ISSUE_URL.format(
                                filename=urllib.quote(filename),
                                urlname=urllib.quote(urlname),
                            ),
                            'name': '<i class=\"fa fa-pencil-square-o fa-lg\"></i> Suggest Edits'
                        }
                    ]
                }
            })


module = SuggestedEditsModule()

if __name__ == '__main__':
    module.test()
