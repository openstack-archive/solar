#!/usr/bin/env python

import os

import click
import yaml
from fnmatch import fnmatch
import shutil

def ensure_dir(dir):
    try:
        os.makedirs(dir)
    except OSError:
        pass

CURDIR = os.path.dirname(os.path.realpath(__file__))

LIBRARY_PATH = os.path.join(CURDIR, 'fuel-library')
RESOURCE_TMP_WORKDIR = os.path.join(CURDIR, 'tmp/resources')
ensure_dir(RESOURCE_TMP_WORKDIR)
RESOURCE_DIR = os.path.join(CURDIR, 'resources')


def clean_resources():
    shutil.rmtree(RESOURCE_TMP_WORKDIR)
    ensure_dir(RESOURCE_TMP_WORKDIR)

class Task(object):

    def __init__(self, task_data, task_path):
        self.data = task_data
        self.src_path = task_path
        self.name = self.data['id']
        self.type = self.data['type']

    @property
    def manifest(self):
        after_naily = self.data['parameters']['puppet_manifest'].split('osnailyfacter/')[-1]
        return os.path.join(
            LIBRARY_PATH, 'deployment', 'puppet', 'osnailyfacter',
            after_naily)

    @property
    def dst_path(self):
        return os.path.join(RESOURCE_TMP_WORKDIR, self.data['id'])

    @property
    def actions_path(self):
        return os.path.join(self.dst_path, 'actions')

    @property
    def meta_path(self):
        return os.path.join(self.dst_path, 'meta.yaml')

    def meta(self):
        data = {'id': self.data['id'],
                'handler': 'puppetv2',
                'version': '8.0',
                'inputs': self.inputs()}
        return yaml.safe_dump(data, default_flow_style=False)

    @property
    def actions(self):
        """yield an iterable of src/dst
        """
        yield self.manifest, os.path.join(self.actions_path, 'run.pp')

    def inputs(self):
        return {}


def get_files(base_dir, file_pattern='*tasks.yaml'):
    for root, _dirs, files in os.walk(base_dir):
        for file_name in files:
            if fnmatch(file_name, file_pattern):
                yield root, file_name

def load_data(base, file_name):
    with open(os.path.join(base, file_name)) as f:
        return yaml.load(f)

def preview(task):
    print 'PATH'
    print task.dst_path
    print 'META'
    print task.meta()
    print 'ACTIONS'
    for action in task.actions():
        print 'src=%s dst=%s' % action

def create(task):
    ensure_dir(task.dst_path)
    ensure_dir(task.actions_path)
    with open(task.meta_path, 'w') as f:
        f.write(task.meta())
    for src, dst in task.actions:
        shutil.copyfile(src, dst)

@click.group()
def main():
    pass

@main.command(help='converts tasks into resources')
@click.argument('tasks', nargs=-1)
@click.option('-t', is_flag=True)
@click.option('-p', is_flag=True)
@click.option('-c', is_flag=True)
def t2r(tasks, t, p, c):
    if c:
        clean_resources()
    for base, task_yaml in get_files(LIBRARY_PATH + '/deployment'):
        for item in load_data(base, task_yaml):
            task = Task(item, base)
            if task.type != 'puppet':
                continue

            if task.name in tasks or tasks == ():
                if p:
                    preview(task)
                else:
                    create(task)

if __name__ == '__main__':
    main()
