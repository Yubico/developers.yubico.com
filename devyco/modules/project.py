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
import os
import json
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
            new_target = path.join(self._target, project_name)
            shutil.move(project, new_target)
            hidden.append(project_name)

            # Create Releases dir if it doesn't exist.
            releases_conf = path.join(new_target, 'Releases', '.conf.json')
            if not path.isfile(releases_conf):
                releases_dir = path.dirname(releases_conf)
                if path.isdir(releases_dir):
                    with open(releases_conf, 'w') as f:
                        json.dump({'releases':{}}, f)

        self._context['dirconfig']['hidden'] = hidden
        shutil.rmtree(path.join(self._target, project_dir))


module = ProjectModule()

if __name__ == '__main__':
    module.test()
