"""
Allows directories to inherit configuration through configuration templates.
"""

from devyco.module import Module
import json


def merge_data(base, added):
    for (key, value) in added.items():
        if key not in base:
            base[key] = value
        else:
            base_value = base[key]
            if isinstance(value, dict):
                if not isinstance(base_value, dict):
                    raise ValueError('Cannot merge data: %r with %r' %
                                     (value, base_value))
                merge_data(base_value, value)
            elif isinstance(value, list):
                if isinstance(base_value, list):
                    base_value.extend(value)
                else:
                    base[key] = [base_value] + value
            else:  # Can't merge, just overwrite
                base[key] = value


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
