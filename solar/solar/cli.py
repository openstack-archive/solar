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

"""Solar CLI api

On create "golden" resource should be moved to special place
"""

import click
import json
import networkx as nx
import os
import pprint
import subprocess
import yaml

from solar import utils
from solar import operations
from solar import state
from solar.core import actions
from solar.core import resource as sresource
from solar.core.resource import assign_resources_to_nodes
from solar.core.resource import connect_resources
from solar.core import signals
from solar.core.tags_set_parser import Expression
from solar.interfaces.db import get_db

# NOTE: these are extensions, they shouldn't be imported here
# Maybe each extension can also extend the CLI with parsers
from solar.extensions.modules.discovery import Discovery


db = get_db()


@click.group()
def main():
    pass


@main.command()
@click.option('-n', '--nodes')
@click.option('-r', '--resources')
def assign(resources, nodes):
    def _get_resources_list():
        result = []
        for path in utils.find_by_mask(utils.read_config()['resources-files-mask']):
            resource = utils.yaml_load(path)
            resource['path'] = path
            resource['dir_path'] = os.path.dirname(path)
            result.append(resource)

        return result

    nodes = filter(
        lambda n: Expression(nodes, n.get('tags', [])).evaluate(),
        db.get_list('nodes'))

    resources = filter(
        lambda r: Expression(resources, r.get('tags', [])).evaluate(),
        _get_resources_list())

    print("For {0} nodes assign {1} resources".format(len(nodes), len(resources)))
    assign_resources_to_nodes(resources, nodes)


@main.command()
@click.option('-p', '--profile')
def connect(profile):
    profile_ = db.get_record('profiles', profile)
    connect_resources(profile_)


@main.command()
def discover():
    Discovery({'id': 'discovery'}).discover()


@main.command()
@click.option('-c', '--create', default=False, is_flag=True)
@click.option('-t', '--tags', multiple=True)
@click.option('-i', '--id')
def profile(id, tags, create):
    if not id:
        id = utils.generate_uuid()
    if create:
        params = {'tags': tags, 'id': id}
        profile_template_path = os.path.join(
            utils.read_config()['template-dir'], 'profile.yml')
        data = yaml.load(utils.render_template(profile_template_path, params))
        db.store('profiles', data)
    else:
        pprint.pprint(db.get_list('profiles'))


@main.command()
@click.option('-t', '--tags')
@click.option('-a', '--action')
def run(action, tags):
    from solar.core import actions
    from solar.core import resource

    resources = filter(
        lambda r: Expression(tags, r.get('tags', [])).evaluate(),
        db.get_list('resource'))

    for resource in resources:
        resource_obj = sresource.load(resource['id'])
        actions.resource_action(resource_obj, action)


def init_cli_resource():
    @main.group()
    def resource():
        pass

    @resource.command()
    @click.argument('resource_path')
    @click.argument('action_name')
    def action(action_name, resource_path):
        print 'action', resource_path, action_name
        r = sresource.load(resource_path)
        actions.resource_action(r, action_name)

    @resource.command()
    @click.argument('name')
    @click.argument('base_path')
    @click.argument('args')
    def create(args, base_path, name):
        print 'create', name, base_path, args
        args = json.loads(args)
        sresource.create(name, base_path, args)

    @resource.command()
    @click.option('--tag', default=None)
    @click.option('--use-json/--no-use-json', default=False)
    @click.option('--color/--no-color', default=True)
    def show(color, use_json, tag):
        resources = []

        for name, res in sresource.load_all().items():
            show = True
            if tag:
                if tag not in res.tags:
                    show = False

            if show:
                resources.append(res)

        if use_json:
            output = json.dumps([r.to_dict() for r in resources], indent=2)
        else:
            if color:
                formatter = lambda r: r.color_repr()
            else:
                formatter = lambda r: unicode(r)
            output = '\n'.join(formatter(r) for r in resources)

        if output:
            click.echo_via_pager(output)


    @resource.command()
    @click.argument('resource_path')
    @click.argument('tag_name')
    @click.option('--add/--delete', default=True)
    def tag(add, tag_name, resource_path):
        print 'Tag', resource_path, tag_name, add
        r = sresource.load(resource_path)
        if add:
            r.add_tag(tag_name)
        else:
            r.remove_tag(tag_name)
        r.save()

    @resource.command()
    @click.argument('name')
    @click.argument('args')
    def update(name, args):
        args = json.loads(args)
        all = sresource.load_all()
        r = all[name]
        r.update(args)


def init_cli_connect():
    @main.command()
    @click.argument('emitter')
    @click.argument('receiver')
    @click.option('--mapping', default=None)
    def connect(mapping, receiver, emitter):
        print 'Connect', emitter, receiver
        emitter = sresource.load(emitter)
        receiver = sresource.load(receiver)
        print emitter
        print receiver
        if mapping is not None:
            mapping = json.loads(mapping)
        signals.connect(emitter, receiver, mapping=mapping)

    @main.command()
    @click.argument('emitter')
    @click.argument('receiver')
    def disconnect(receiver, emitter):
        print 'Disconnect', emitter, receiver
        emitter = sresource.load(emitter)
        receiver = sresource.load(receiver)
        print emitter
        print receiver
        signals.disconnect(emitter, receiver)


def init_changes():
    @main.group()
    def changes():
        pass

    @changes.command()
    def stage():
        log = operations.stage_changes()
        print log.show()

    @changes.command()
    @click.option('--one', is_flag=True, default=False)
    def commit(one):
        if one:
            operations.commit_one()
        else:
            operations.commit_changes()

    @changes.command()
    @click.option('--limit', default=5)
    def history(limit):
        print state.CL().show()

    @changes.command()
    @click.option('--last', is_flag=True, default=False)
    @click.option('--all', is_flag=True, default=False)
    @click.option('--uid', default=None)
    def rollback(last, all, uid):
        if last:
            print operations.rollback_last()
        elif all:
            print operations.rollback_all()
        elif uid:
            print operations.rollback_uid(uid)


def init_cli_connections():
    @main.group()
    def connections():
        pass

    @connections.command()
    def show():
        print json.dumps(signals.CLIENTS, indent=2)

    # TODO: this requires graphing libraries
    @connections.command()
    def graph():
        #g = xs.connection_graph()
        g = signals.detailed_connection_graph()

        nx.write_dot(g, 'graph.dot')
        subprocess.call(['dot', '-Tpng', 'graph.dot', '-o', 'graph.png'])

        # Matplotlib
        #pos = nx.spring_layout(g)
        #nx.draw_networkx_nodes(g, pos)
        #nx.draw_networkx_edges(g, pos, arrows=True)
        #nx.draw_networkx_labels(g, pos)
        #plt.axis('off')
        #plt.savefig('graph.png')


def init_cli_deployment_config():
    @main.command()
    @click.argument('filepath')
    def deploy(filepath):
        print 'Deploying from file {}'.format(filepath)
        xd.deploy(filepath)


def run():
    init_cli_resource()
    init_cli_connect()
    init_cli_connections()
    init_cli_deployment_config()
    init_changes()

    main()


if __name__ == '__main__':
    run()
