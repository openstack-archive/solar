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
from solar.interfaces import orm
from solar import utils

from solar.cli import base
from solar.cli import executors
from solar.cli.orch import orchestration
from solar.cli.system_log import changes
from solar.cli.events import events
from solar.cli.resource import resource as cli_resource


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
                        for r in emitter_input.receivers.as_set()
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
        if dry_run:
            dry_run_executor = executors.DryRunExecutor(mapping=json.loads(dry_run_mapping))

        resources = filter(
            lambda r: Expression(tags, r.tags).evaluate(),
            orm.DBResource.all()
        )

        for r in resources:
            resource_obj = sresource.load(r['id'])
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

    @connections.command()
    @click.option('--start-with', default=None)
    @click.option('--end-with', default=None)
    def graph(start_with, end_with):
        g = signals.detailed_connection_graph(start_with=start_with,
                                              end_with=end_with)

        nx.write_dot(g, 'graph.dot')
        fabric_api.local('dot -Tsvg graph.dot -o graph.svg')


def run():
    init_actions()
    init_cli_connect()
    init_cli_connections()

    main.add_command(cli_resource)
    main.add_command(orchestration)
    main.add_command(changes)
    main.add_command(events)
    main()


if __name__ == '__main__':
    run()
