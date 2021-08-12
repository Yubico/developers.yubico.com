"""
Allows directories to inherit configuration through configuration templates.
"""

from devyco.module import Module, merge_data
import json


class TemplateModule(Module):

    def __init__(self):
        super(TemplateModule, self).__init__()
        self._templates = {}

    def _run(self):
        conf = self.get_conf('template')
        if conf is None:
            return

        for (name, template) in conf.get('define', {}).items():
            self._define(name, template)

        if 'inherit' in conf:
            self._inherit(conf['inherit'])

    def _define(self, name, template):
        self._templates[name] = json.dumps(template)

    def _inherit(self, inherit):
        conf = {}
        for (name, data) in inherit.items():
            merge_data(conf, json.loads(self._templates[name] % data))
        merge_data(conf, self._context['dirconfig'])
        self._context['dirconfig'] = conf


module = TemplateModule()

if __name__ == '__main__':
    module.test()
