"""
Generates data from a project directory.
Activated by a "project" entry in a .conf.json file, containing the following
settings:
    index: File to use as index page (optional, defaults to "README")
    documents: File pattern of documents (optional, defaults to "doc/*")

TODO: Read BLURB file and add additional stuff to index page (GitHub, TravisCI,
license, etc.).
"""

import shutil
from os import path
from devyco.module import Module


class ProjectModule(Module):

    def _run(self):
        project_dir = self.get_conf('project')
        if project_dir is None:
            return
        hidden = self._context['dirconfig'].get('hidden', [])

        for project in self.list_files('*', project_dir):
            project_name = path.basename(project)
            shutil.move(project, path.join(self._target, project_name))
            hidden.append(project_name)

        self._context['dirconfig']['hidden'] = hidden
        shutil.rmtree(path.join(self._target, project_dir))


module = ProjectModule()

if __name__ == '__main__':
    module.test()
