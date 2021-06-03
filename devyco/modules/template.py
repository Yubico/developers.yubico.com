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
        template_data = {k: v for (k, v) in template.items() if not k.startswith('_')}
        default_data = template.get('_defaults', {})
        self._templates[name] = (json.dumps(template_data), default_data)

    def _inherit(self, inherit):
        conf = {}
        for (name, data) in inherit.items():
            template_json, default_data = self._templates[name]
            for k, v in default_data.items():
                if k not in data:
                    data[k] = v
            merge_data(conf, json.loads(template_json % data))
        merge_data(conf, self._context['dirconfig'])
        self._context['dirconfig'] = conf


module = TemplateModule()

if __name__ == '__main__':
    module.test()
