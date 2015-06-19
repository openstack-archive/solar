import os
import subprocess

from solar import utils


class BaseProvider(object):
    def run(self):
        pass


class DirectoryProvider(BaseProvider):
    def __init__(self, directory):
        self.directory = directory


class GitProvider(BaseProvider):
    def __init__(self, repository, path='.'):
        self.repository = repository
        self.path = path

        repo_name = os.path.split(self.repository)[1]

        resources_directory = os.path.join(
            utils.read_config()['resources-directory'],
            repo_name
        )

        with open('/tmp/git-provider.yaml', 'w') as f:
            f.write("""
---

- hosts: all
  tasks:
    - git: repo={repository} dest={destination} clone={clone} update=yes
            """.format(
                repository=self.repository,
                destination=resources_directory,
                clone='no' if os.path.exists(resources_directory) else 'yes'
            ))

        subprocess.check_call([
            'ansible-playbook',
            '-i', '"localhost,"',
            '-c', 'local',
            '/tmp/git-provider.yaml'
        ])

        if path != '.':
            self.directory = os.path.join(resources_directory, path)
        else:
            self.directory = resources_directory
