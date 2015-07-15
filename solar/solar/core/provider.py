from fabric import api as fabric_api
import os
import requests
import StringIO
import zipfile

from solar import utils


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
        self.branch = 'master'
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
            f.write("""
---
- hosts: all
  tasks:
    - git: repo={repository} dest={destination} clone={clone} update=yes version={branch}
            """.format(
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
