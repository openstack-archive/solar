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
from fabric import api as fabric_api
import json
import networkx as nx
import os
import pprint
import sys
import tabulate
import yaml

from solar import utils
from solar import operations
from solar import state
from solar.core import actions
from solar.core import resource as sresource
from solar.core.resource import assign_resources_to_nodes
from solar.core import signals
from solar.core.tags_set_parser import Expression
from solar.core import testing
from solar.core.resource import virtual_resource as vr
from solar.interfaces.db import get_db

from solar.cli.orch import orchestration

# NOTE: these are extensions, they shouldn't be imported here
# Maybe each extension can also extend the CLI with parsers
from solar.extensions.modules.discovery import Discovery


db = get_db()


# HELPERS
def format_resource_input(resource_name, resource_input_name):
    return '{}::{}'.format(
        #click.style(resource_name, fg='white', bold=True),
        resource_name,
        click.style(resource_input_name, fg='yellow')
    )

def show_emitter_connections(emitter_name, destinations):
    inputs = sorted(destinations)

    for emitter_input in inputs:
        click.echo(
            '{} -> {}'.format(
                format_resource_input(emitter_name, emitter_input),
                '[{}]'.format(
                    ', '.join(
                        format_resource_input(*r)
                        for r in destinations[emitter_input]
                    )
                )
            )
        )


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

    click.echo(
        "For {0} nodes assign {1} resources".format(len(nodes), len(resources))
    )
    assign_resources_to_nodes(resources, nodes)


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


def init_actions():
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


def init_changes():
    @main.group()
    def changes():
        pass

    @changes.command()
    def validate():
        errors = vr.validate_resources()
        if errors:
            for r, error in errors:
                print 'ERROR: %s: %s' % (r.name, error)
            sys.exit(1)

    @changes.command()
    def stage():
        log = operations.stage_changes()
        click.echo(log.show())

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
        click.echo(state.CL().show())

    @changes.command()
    @click.option('--last', is_flag=True, default=False)
    @click.option('--all', is_flag=True, default=False)
    @click.option('--uid', default=None)
    def rollback(last, all, uid):
        if last:
            click.echo(operations.rollback_last())
        elif all:
            click.echo(operations.rollback_all())
        elif uid:
            click.echo(operations.rollback_uid(uid))

    @changes.command()
    def test():
        testing.test_all()


def init_cli_connect():
    @main.command()
    @click.argument('emitter')
    @click.argument('receiver')
    @click.argument('mapping', default='')
    def connect(mapping, receiver, emitter):
        mapping_parsed = {}

        click.echo('Connect {} to {}'.format(emitter, receiver))
        emitter = sresource.load(emitter)
        receiver = sresource.load(receiver)
        try:
            mapping_parsed.update(json.loads(mapping))
        except ValueError:
            for m in mapping.split():
                k, v = m.split('->')
                mapping_parsed.update({k: v})
        signals.connect(emitter, receiver, mapping=mapping_parsed)

        clients = signals.Connections.read_clients()
        show_emitter_connections(emitter.name, clients[emitter.name])

    @main.command()
    @click.argument('emitter')
    @click.argument('receiver')
    def disconnect(receiver, emitter):
        click.echo('Disconnect {} from {}'.format(emitter, receiver))
        emitter = sresource.load(emitter)
        receiver = sresource.load(receiver)
        click.echo(emitter)
        click.echo(receiver)
        signals.disconnect(emitter, receiver)

        clients = signals.Connections.read_clients()
        show_emitter_connections(emitter.name, clients[emitter.name])


def init_cli_connections():
    @main.group()
    def connections():
        pass

    @connections.command()
    def clear_all():
        click.echo('Clearing all connections')
        signals.Connections.clear()

    @connections.command()
    def show():
        clients = signals.Connections.read_clients()
        keys = sorted(clients)
        for emitter_name in keys:
            show_emitter_connections(emitter_name, clients[emitter_name])

    # TODO: this requires graphing libraries
    @connections.command()
    @click.option('--start-with', default=None)
    @click.option('--end-with', default=None)
    def graph(end_with, start_with):
        #g = xs.connection_graph()
        g = signals.detailed_connection_graph(start_with=start_with,
                                              end_with=end_with)

        nx.write_dot(g, 'graph.dot')
        fabric_api.local('dot -Tpng graph.dot -o graph.png')

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
        click.echo('Deploying from file {}'.format(filepath))
        xd.deploy(filepath)


def init_cli_resource():
    @main.group()
    def resource():
        pass

    @resource.command()
    @click.argument('action')
    @click.argument('resource')
    def action(action, resource):
        click.echo(
            'action {} for resource {}'.format(action, resource)
        )
        actions.resource_action(sresource.load(resource), action)


    @resource.command()
    def compile_all():
        from solar.core.resource import compiler

        destination_path = utils.read_config()['resources-compiled-file']

        if os.path.exists(destination_path):
            os.remove(destination_path)

        for path in utils.find_by_mask(utils.read_config()['resources-files-mask']):
            meta = utils.yaml_load(path)
            meta['base_path'] = os.path.dirname(path)

            compiler.compile(meta)

    @resource.command()
    def clear_all():
        click.echo('Clearing all resources')
        db.clear()

    @resource.command()
    @click.argument('name')
    @click.argument('base_path', type=click.Path(exists=True, file_okay=True))
    @click.argument('args', nargs=-1)
    def create(args, base_path, name):
        args_parsed = {}

        click.echo('create {} {} {}'.format(name, base_path, args))
        for arg in args:
            try:
                args_parsed.update(json.loads(arg))
            except ValueError:
                k, v = arg.split('=')
                args_parsed.update({k: v})
        resources = vr.create(name, base_path, args_parsed)
        for res in resources:
            click.echo(res.color_repr())

    @resource.command()
    @click.option('--name', default=None)
    @click.option('--tag', default=None)
    @click.option('--json', default=False, is_flag=True)
    @click.option('--color', default=True, is_flag=True)
    def show(**kwargs):
        resources = []

        for name, res in sresource.load_all().items():
            show = True
            if kwargs['tag']:
                if kwargs['tag'] not in res.tags:
                    show = False
            if kwargs['name']:
                if res.name != kwargs['name']:
                    show = False

            if show:
                resources.append(res)

        echo = click.echo_via_pager
        if kwargs['json']:
            output = json.dumps([r.to_dict() for r in resources], indent=2)
            echo = click.echo
        else:
            if kwargs['color']:
                formatter = lambda r: r.color_repr()
            else:
                formatter = lambda r: unicode(r)
            output = '\n'.join(formatter(r) for r in resources)

        if output:
            echo(output)


    @resource.command()
    @click.argument('resource_name')
    @click.argument('tag_name')
    @click.option('--add/--delete', default=True)
    def tag(add, tag_name, resource_name):
        click.echo('Tag {} with {} {}'.format(resource_name, tag_name, add))
        r = sresource.load(resource_name)
        if add:
            r.add_tag(tag_name)
        else:
            r.remove_tag(tag_name)
        r.save()

    @resource.command()
    @click.argument('name')
    @click.argument('args', nargs=-1)
    def update(name, args):
        args_parsed = {}
        for arg in args:
            try:
                args_parsed.update(json.loads(arg))
            except ValueError:
                k, v = arg.split('=')
                args_parsed.update({k: v})
        click.echo('Updating resource {} with args {}'.format(name, args_parsed))
        all = sresource.load_all()
        r = all[name]
        r.update(args_parsed)

    @resource.command()
    @click.option('--check-missing-connections', default=False, is_flag=True)
    def validate(check_missing_connections):
        errors = vr.validate_resources()
        for r, error in errors:
            click.echo('ERROR: %s: %s' % (r.name, error))

        if check_missing_connections:
            missing_connections = vr.find_missing_connections()
            if missing_connections:
                click.echo(
                    'The following resources have inputs of the same value '
                    'but are not connected:'
                )
                click.echo(
                    tabulate.tabulate([
                        ['%s::%s' % (r1, i1), '%s::%s' % (r2, i2)]
                        for r1, i1, r2, i2 in missing_connections
                    ])
                )

    @resource.command()
    @click.argument('path', type=click.Path(exists=True, dir_okay=False))
    def get_inputs(path):
        with open(path) as f:
            content = f.read()
        print vr.get_inputs(content)


def run():
    init_actions()
    init_changes()
    init_cli_connect()
    init_cli_connections()
    init_cli_deployment_config()
    init_cli_resource()

    main.add_command(orchestration)
    main()


if __name__ == '__main__':
    run()
