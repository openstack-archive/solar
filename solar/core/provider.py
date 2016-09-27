#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import warnings

warnings.warn("For now this file is deprecated "
              "in future it will be part of Solar repository logic",
              DeprecationWarning)

from fabric import api as fabric_api
import os
import requests
import StringIO
import zipfile

from solar import utils

GIT_TPL = """
---
- hosts: all
  tasks:
    - git: repo={repository}
           dest={destination}
           clone={clone}
           update=yes
           version={branch}
"""


class BaseProvider(object):

    def __init__(self, base_path=None):
        if base_path is None:
            self.base_path = utils.read_config()['resources-directory']
        else:
            self.base_path = base_path

    def run(self):
        pass


class DirectoryProvider(BaseProvider):

    def __init__(self, directory, *args, **kwargs):
        self.directory = directory

        super(DirectoryProvider, self).__init__(*args, **kwargs)


class GitProvider(BaseProvider):

    def __init__(self, repository, branch='master', path='.', *args, **kwargs):
        super(GitProvider, self).__init__(*args, **kwargs)

        self.repository = repository
        self.branch = branch
        self.path = path

        directory = self._directory()

        if not os.path.exists(directory):
            self._clone_repo()

        if path != '.':
            self.directory = os.path.join(directory, path)
        else:
            self.directory = directory

    def _directory(self):
        repo_name = os.path.split(self.repository)[1]

        return os.path.join(
            self.base_path,
            repo_name
        )

    def _clone_repo(self):
        directory = self._directory()

        with open('/tmp/git-provider.yaml', 'w') as f:
            f.write(GIT_TPL.format(
                repository=self.repository,
                branch=self.branch,
                destination=directory,
                clone='yes'
            ))

        fabric_api.local(
            'ansible-playbook -i "localhost," -c local /tmp/git-provider.yaml'
        )


class RemoteZipProvider(BaseProvider):
    """Download & extract zip from some URL.

    Assumes zip structure of the form:
    <group-name>
      <resource1>
      <resource2>
      ...
    """

    def __init__(self, url, path='.', *args, **kwargs):
        super(RemoteZipProvider, self).__init__(*args, **kwargs)

        self.url = url
        self.path = path

        r = requests.get(url)
        s = StringIO.StringIO(r.content)
        z = zipfile.ZipFile(s)

        group_name = os.path.dirname(z.namelist()[0])
        directory = os.path.join(
            self.base_path, group_name
        )
        if not os.path.exists(directory):
            z.extractall(self.base_path)

        if path != '.':
            self.directory = os.path.join(directory, path)
        else:
            self.directory = directory


class SVNProvider(BaseProvider):
    """With git you can't checkout only directory from repo,

    but with svn you can
    """

    def __init__(self, url, path='.', base_path=None):
        self.url = url
        self.path = path
        self.base_path = base_path or utils.read_config()[
            'resources-directory']
        if path != '.':
            self.repo_directory = os.path.join(self.base_path, path)
        else:
            self.repo_directory = self.base_path
        self.directory = os.path.join(
            self.repo_directory, self.url.rsplit('/', 1)[-1])

    def run(self):
        if not os.path.exists(self.repo_directory):
            os.makedirs(self.repo_directory)

        if not os.path.exists(self.directory):
            fabric_api.local(
                'cd {dir} && svn checkout {url}'.format(
                    dir=self.repo_directory,
                    url=self.url))
