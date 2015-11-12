#!/usr/bin/env python

import os
from fnmatch import fnmatch
import shutil
from collections import OrderedDict

import click
import yaml
import networkx as nx


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
VR_TMP_DIR = os.path.join(CURDIR, 'tmp/vrs')
ensure_dir(VR_TMP_DIR)
INPUTS_LOCATION = "/root/latest/"
DEPLOYMENT_GROUP_PATH = os.path.join(LIBRARY_PATH,
    'deployment', 'puppet', 'deployment_groups', 'tasks.yaml')

def clean_resources():
    shutil.rmtree(RESOURCE_TMP_WORKDIR)
    ensure_dir(RESOURCE_TMP_WORKDIR)

def clean_vr():
    shutil.rmtree(VR_TMP_DIR)
    ensure_dir(VR_TMP_DIR)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    class OrderedDumper(Dumper):
        pass
    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


class Task(object):

    def __init__(self, task_data, task_path):
        self.data = task_data
        self.src_path = task_path
        self.name = self.data['id']
        self.type = self.data['type']

    def edges(self):
        data = self.data
        if 'required_for' in data:
            for req in data['required_for']:
                yield self.name, req
        if 'requires' in data:
            for req in data['requires']:
                yield req, self.name

        if 'groups' in data:
            for req in data['groups']:
                yield self.name, req
        if 'tasks' in data:
            for req in data['tasks']:
                yield req, self.name

    @property
    def manifest(self):
        after_naily = self.data['parameters']['puppet_manifest'].split('osnailyfacter/')[-1]
        return os.path.join(
            LIBRARY_PATH, 'deployment', 'puppet', 'osnailyfacter',
            after_naily)

    @property
    def spec_name(self):
        splitted = self.data['parameters']['puppet_manifest'].split('/')
        directory = splitted[-2]
        name = splitted[-1].split('.')[0]
        return "{}_{}_spec.rb'".format(directory, name)

    @property
    def dst_path(self):
        return os.path.join(RESOURCE_TMP_WORKDIR, self.name)

    @property
    def actions_path(self):
        return os.path.join(self.dst_path, 'actions')

    @property
    def meta_path(self):
        return os.path.join(self.dst_path, 'meta.yaml')

    def meta(self):
        data = OrderedDict([('id', self.name),
                ('handler', 'puppetv2'),
                ('version', '8.0'),
                ('actions', {
                    'run': 'run.pp',
                    'update': 'run.pp'}),
                ('input', self.inputs()),])
        return ordered_dump(data, default_flow_style=False)

    @property
    def actions(self):
        """yield an iterable of src/dst
        """
        yield self.manifest, os.path.join(self.actions_path, 'run.pp')

    def inputs(self):
        """
        Inputs prepared by

        fuel_noop_tests.rb
        identity = spec.split('/')[-1]
        ENV["SPEC"] = identity

        hiera.rb
        File.open("/tmp/fuel_specs/#{ENV['SPEC']}", 'a') { |f| f << "- #{key}\n" }
        """
        print self.spec_name
        lookup_stack_path = os.path.join(
            INPUTS_LOCATION, self.spec_name)
        if not os.path.exists(lookup_stack_path):
            return {}

        with open(lookup_stack_path) as f:
            data = yaml.safe_load(f) or []
        data = data + ['puppet_modules']
        return {key: {'value': None} for key
                in set(data) if '::' not in key}


class RoleData(Task):

    name = 'role_data'

    def meta(self):
        data = {'id': self.name,
                'handler': 'puppetv2',
                'version': '8.0',
                'inputs': self.inputs(),
                'manager': 'globals.py'}
        return yaml.safe_dump(data, default_flow_style=False)

    @property
    def actions(self):
        pass


class DGroup(object):

    filtered = ['globals', 'hiera', 'deploy_start']

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

    def resources(self):

        yield OrderedDict(
                [('id', RoleData.name+"{{index}}"),
                 ('from', 'f2s/resources/'+RoleData.name),
                 ('location', "{{node}}"),
                 ('values', {'uid': '{{index}}',
                             'env': '{{env}}',
                             'puppet_modules': '/etc/puppet/modules'})])

        for t, _, _ in self.tasks:
            if t.name in self.filtered:
                continue

            yield OrderedDict(
                [('id', t.name+"{{index}}"),
                 ('from', 'f2s/resources/'+t.name),
                 ('location', "{{node}}"),
                 ('values_from', RoleData.name+"{{index}}")])


    def events(self):
        for t, inner, outer in self.tasks:
            if t.name in self.filtered:
                continue

            yield OrderedDict([
                    ('type', 'depends_on'),
                    ('state', 'success'),
                    ('parent_action', RoleData.name + '{{index}}.run'),
                    ('depend_action', t.name + '{{index}}.run')])

            for dep in set(inner):
                if dep in self.filtered:
                    continue

                yield OrderedDict([
                    ('type', 'depends_on'),
                    ('state', 'success'),
                    ('parent_action', dep + '{{index}}.run'),
                    ('depend_action', t.name + '{{index}}.run')])
            for dep in set(outer):
                if dep in self.filtered:
                    continue

                yield OrderedDict([
                    ('type', 'depends_on'),
                    ('state', 'success'),
                    ('parent', {
                        'with_tags': ['resource=' + dep],
                        'action': 'run'}),
                    ('depend_action', t.name + '{{index}}.run')])

    def meta(self):
        data = OrderedDict([
            ('id', self.name),
            ('resources', list(self.resources())),
            ('events', list(self.events()))])
        return ordered_dump(data, default_flow_style=False)

    @property
    def path(self):
        return os.path.join(VR_TMP_DIR, self.name + '.yml')


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
    if task.actions_path:
        ensure_dir(task.actions_path)
        for src, dst in task.actions:
            shutil.copyfile(src, dst)

    with open(task.meta_path, 'w') as f:
        f.write(task.meta())


def get_tasks():
    for base, task_yaml in get_files(LIBRARY_PATH + '/deployment'):
        for item in load_data(base, task_yaml):
            yield Task(item, base)


def get_graph():
    dg = nx.DiGraph()
    for t in get_tasks():
        dg.add_edges_from(list(t.edges()))
        dg.add_node(t.name, t=t)
    return dg

def dgroup_subgraph(dg, dgroup):
    preds = [p for p in dg.predecessors(dgroup)
             if dg.node[p]['t'].type == 'puppet']
    return dg.subgraph(preds)

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

    for task in get_tasks():
        if task.type != 'puppet':
            continue

        if task.name in tasks or tasks == ():
            if p:
                preview(task)
            else:
                create(task)


@main.command(help='convert groups into templates')
@click.argument('groups', nargs=-1)
@click.option('-c', is_flag=True)
def g2vr(groups, c):
    if c:
        clean_vr()

    dg = get_graph()
    dgroups = [n for n in dg if dg.node[n]['t'].type == 'group']

    for group in dgroups:
        if groups and group not in groups:
            continue

        ordered = []
        dsub = dg.subgraph(dg.predecessors(group))
        for t in nx.topological_sort(dsub):
            inner_preds = []
            outer_preds = []
            for p in dg.predecessors(t):
                if dg.node[p]['t'].type != 'puppet':
                    continue

                if p in dsub:
                    inner_preds.append(p)
                else:
                    outer_preds.append(p)

            if dg.node[t]['t'].type == 'puppet':
                ordered.append((dg.node[t]['t'], inner_preds, outer_preds))

        obj = DGroup(group, ordered)
        with open(obj.path, 'w') as f:
            f.write(obj.meta())
        # based on inner/outer aggregation configure joins in events

if __name__ == '__main__':
    main()
