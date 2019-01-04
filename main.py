#!/usr/bin/env python
"""This is a test"""

import argparse
import os
import xml.dom.minidom
import pathlib


class Project:
    """Minimal IntelliJ Project folder"""

    def __init__(self, path):
        self.path = path
        self.project = pathlib.Path(path).stem
        self.vcs_file = os.path.join(path, '.idea', 'vcs.xml')
        self.mod_file = os.path.join(path, '.idea', 'modules.xml')
        self.proj_file = os.path.join(path, '.idea', f'{self.project}.iml')

    def create(self):
        """Create vcs, module and project folder"""
        idea_folder = pathlib.Path(self.vcs_file).parent
        if not os.path.exists(idea_folder):
            os.makedirs(idea_folder)
        self.create_project_file()
        self.create_vcs_file()
        self.create_mod_file()

    def create_vcs_file(self):
        template = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="VcsDirectoryMappings">
    <!-- <mapping directory="$PROJECT_DIR$/../../brad.beyenhof/documentation" vcs="Git" /> -->
  </component>
</project>"""
        with open(self.vcs_file, 'w') as vcs_file:
            vcs_file.write(template)

    def create_mod_file(self):
        template = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectModuleManager">
    <modules>
      <!--- <module fileurl="file://$PROJECT_DIR$/../../cobbler-2.6/cobbler-2.6.iml" filepath="$PROJECT_DIR$/../../cobbler-2.6/cobbler-2.6.iml" /> -->
    </modules>
  </component>
</project>"""
        with open(self.mod_file, 'w') as mod_file:
            mod_file.write(template)

    def create_project_file(self):
        template = """<?xml version="1.0" encoding="UTF-8"?>
<module type="JAVA_MODULE" version="4">
  <component name="NewModuleRootManager" inherit-compiler-output="true">
    <exclude-output />
    <content url="file://$MODULE_DIR$" />
    <orderEntry type="inheritedJdk" />
    <orderEntry type="sourceFolder" forTests="false" />
  </component>
</module>"""
        with open(self.proj_file, 'w') as proj_file:
            proj_file.write(template)


class VCSFile:
    """Represents a project's vcs.xml file"""

    def __init__(self, path):
        self.vcs_path = path
        self.mappings_directories = set()
        self.project_dir = str(pathlib.Path(self.vcs_path).parent.parent)

    def add(self, repo_path):
        path = str(pathlib.Path(repo_path).parent)
        self.mappings_directories.add(path)

    def save(self):
        root = xml.dom.minidom.parse(self.vcs_path)
        comp = root.getElementsByTagName('component')[0]

        for directory in self.mappings_directories:
            elm = xml.dom.minidom.Document().createElement("mapping")
            elm.setAttribute('directory', directory)
            elm.setAttribute('vcs', 'Git')
            comp.appendChild(elm)

        with open(self.vcs_path, 'w') as vcs_file:
            vcs_file.write(root.toprettyxml())

    def load(self):
        root = xml.dom.minidom.parse(self.vcs_path)

        for mapping in root.getElementsByTagName('mapping'):
            _dir = mapping.getAttribute('directory')
            _dir = self.expand_path(_dir)
            self.mappings_directories.add(_dir)

    def expand_path(self, path):
        return path.replace('$PROJECT_DIR$', self.project_dir)


class IMLFile:
    """Represents a project's .iml file"""

    def __init__(self):
        pass

    @classmethod
    def iml_file_path(cls, git_repo_path):
        path = pathlib.Path(IMLFile.new_path(git_repo_path))
        return f'{path}/{path.stem}.iml'

    @classmethod
    def new_path(cls, repo_path):
        return pathlib.Path(repo_path).parent

    @classmethod
    def create_iml_from_repo_path(cls, path):
        template = """<?xml version="1.0" encoding="UTF-8"?>
    <module type="WEB_MODULE" version="4">
      <component name="NewModuleRootManager" inherit-compiler-output="true">
        <exclude-output />
        <content url="file://$MODULE_DIR$" />
        <orderEntry type="inheritedJdk" />
        <orderEntry type="sourceFolder" forTests="false" />
      </component>
    </module>"""
        iml = IMLFile.iml_file_path(path)
        if not os.path.exists(iml):
            with open(iml, 'w') as iml_file:
                iml_file.write(template)
        return iml


class IntelliJModuleElement:
    """One element in modules.xml file"""

    def __init__(self, iml_path):
        elm = xml.dom.minidom.Document().createElement("module")
        path = IMLFile.iml_file_path(iml_path)
        elm.setAttribute('fileurl', f'file://{path}')
        elm.setAttribute('filepath', f'{path}')
        self.elm = elm


class IntelliJModulesFile:
    """Represents a project's modules.xml file"""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.modules = set()

    def save(self):
        root = xml.dom.minidom.parse(str(self.path))

        for mod in self.modules:
            root.getElementsByTagName('modules')[0].appendChild(mod)

        with open(self.path, 'w') as mod_file:
            mod_file.write(root.toprettyxml())

    def add_module(self, git_path):
        elm = xml.dom.minidom.Document().createElement("module")
        iml_path = pathlib.Path(IMLFile.iml_file_path(git_path))
        elm.setAttribute('fileurl', f'file://{iml_path}')
        elm.setAttribute('filepath', f'{iml_path}')
        self.modules.add(elm)


class Orchestrator:
    """Put it all together"""

    def __init__(self, mod, vcs, repo_paths):
        self.mod = mod
        self.vcs = vcs
        self.repo_paths = repo_paths

    def update_modules(self, repo_paths):
        """Add repo_paths to mod"""
        for repo in repo_paths:
            self.mod.add_module(repo)
        self.mod.save()

    def update_vcs(self, repo_paths):
        """Add repo_paths to vcs.xml"""
        for repo in repo_paths:
            self.vcs.add(repo)
        self.vcs.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repos_list", required=True,
                        help="path to git repo path list as file")
    parser.add_argument("-p", "--project", required=True,
                        help="path to Intellij project folder")
    args = parser.parse_args()

    proj = Project(args.project)
    proj.create()

    with open(args.repos_list) as repos_list_file:
        repo_paths = [i.rstrip() for i in repos_list_file.readlines()]

    for repo_path in repo_paths:
        IMLFile.create_iml_from_repo_path(repo_path)

    mod = IntelliJModulesFile(proj.mod_file)
    vcs = VCSFile(proj.vcs_file)
    orch = Orchestrator(mod, vcs, repo_paths)
    orch.update_modules(repo_paths)
    orch.update_vcs(repo_paths)


if __name__ == "__main__":
    main()
