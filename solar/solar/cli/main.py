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

from solar.core import actions
from solar.core import resource as sresource
from solar.core import signals
from solar.core.tags_set_parser import Expression
from solar.core.resource import virtual_resource as vr
from solar.core.log import log
from solar import errors
from solar.interfaces.db import get_db
from solar.interfaces import orm
from solar import utils

from solar.cli import base
from solar.cli import executors
from solar.cli.orch import orchestration
from solar.cli.system_log import changes
from solar.cli.events import events


db = get_db()


# HELPERS
def format_resource_input(resource_input):
    return '{}::{}'.format(
        #click.style(resource_name, fg='white', bold=True),
        resource_input.resource.name,
        click.style(resource_input.name, fg='yellow')
    )


def show_emitter_connections(emitter):
    for emitter_input in emitter.resource_inputs().values():
        click.echo(
            '{} -> {}'.format(
                format_resource_input(emitter_input),
                '[{}]'.format(
                    ', '.join(
                        format_resource_input(r)
                        for r in emitter_input.receivers.value
                    )
                )
            )
        )


@click.group(cls=base.AliasedGroup)
def main():
    pass


def init_actions():
    @main.command()
    @click.option('-t', '--tags')
    @click.option('-a', '--action')
    @click.option('-d', '--dry-run', default=False, is_flag=True)
    @click.option('-m', '--dry-run-mapping', default='{}')
    def run(dry_run_mapping, dry_run, action, tags):
        from solar.core import actions
        from solar.core import resource

        if dry_run:
            dry_run_executor = executors.DryRunExecutor(mapping=json.loads(dry_run_mapping))

        resources = filter(
            lambda r: Expression(tags, r.get('tags', [])).evaluate(),
            db.get_list('resource'))

        for resource in resources:
            resource_obj = sresource.load(resource['id'])
            actions.resource_action(resource_obj, action)

        if dry_run:
            click.echo('EXECUTED:')
            for key in dry_run_executor.executed:
                click.echo('{}: {}'.format(
                    click.style(dry_run_executor.compute_hash(key), fg='green'),
                    str(key)
                ))


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

        show_emitter_connections(emitter)

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

        show_emitter_connections(emitter)


def init_cli_connections():
    @main.group()
    def connections():
        pass

    @connections.command()
    def show():
        resources = sresource.load_all()
        for r in resources:
            show_emitter_connections(r)

    # TODO: this requires graphing libraries
    @connections.command()
    @click.option('--start-with', default=None)
    @click.option('--end-with', default=None)
    def graph(start_with, end_with):
        g = signals.detailed_connection_graph(start_with=start_with,
                                              end_with=end_with)

        nx.write_dot(g, 'graph.dot')
        fabric_api.local('dot -Tpng graph.dot -o graph.png')


def init_cli_resource():
    @main.group()
    def resource():
        pass

    @resource.command()
    @click.argument('action')
    @click.argument('resource')
    @click.option('-d', '--dry-run', default=False, is_flag=True)
    @click.option('-m', '--dry-run-mapping', default='{}')
    def action(dry_run_mapping, dry_run, action, resource):
        if dry_run:
            dry_run_executor = executors.DryRunExecutor(mapping=json.loads(dry_run_mapping))

        click.echo(
            'action {} for resource {}'.format(action, resource)
        )

        r = sresource.load(resource)
        try:
            actions.resource_action(r, action)
        except errors.SolarError as e:
            log.debug(e)
            sys.exit(1)

        if dry_run:
            click.echo('EXECUTED:')
            for key in dry_run_executor.executed:
                click.echo('{}: {}'.format(
                    click.style(dry_run_executor.compute_hash(key), fg='green'),
                    str(key)
                ))

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
    @click.argument(
        'base_path', type=click.Path(exists=True, resolve_path=True))
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

        for res in sresource.load_all():
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
        # TODO: the above functions should save resource automatically to the DB

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
        res = sresource.load(name)
        res.update(args_parsed)

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
    init_cli_connect()
    init_cli_connections()
    init_cli_resource()

    main.add_command(orchestration)
    main.add_command(changes)
    main.add_command(events)
    main()


if __name__ == '__main__':
    run()
