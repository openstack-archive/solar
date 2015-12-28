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

import collections
import json

import click
from fabric import api as fabric_api
import networkx as nx

from solar.core import resource as sresource
from solar.core import signals

from solar.cli import base
from solar.cli.events import events
from solar.cli.inputs import inputs as cli_inputs
from solar.cli.orch import orchestration
from solar.cli.repository import repository as cli_repository
from solar.cli.resource import resource as cli_resource
from solar.cli.system_log import changes


# HELPERS
def format_resource_input(resource_name, resource_input):
    return '{}::{}'.format(
        resource_name,
        click.style(resource_input, fg='yellow')
    )


def show_emitter_connections(res):
    db_obj = res.db_obj
    d = collections.defaultdict(list)
    for emitter, receiver, _meta in db_obj.inputs._edges():
        d[emitter].append(receiver)

    for emitter, receivers in d.iteritems():
        click.echo("{} -> {}".format(
            format_resource_input(*emitter),
            '[{}]'.format(', '.join(
                format_resource_input(*recv) for recv in receivers))))


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
        raise NotImplementedError("Not yet implemented")
        # if dry_run:
        #     dry_run_executor = executors.DryRunExecutor(
        #                mapping=json.loads(dry_run_mapping))

        # resources = filter(
        #     lambda r: Expression(tags, r.tags).evaluate(),
        #     orm.DBResource.all()
        # )

        # for r in resources:
        #     resource_obj = sresource.load(r['id'])
        #     actions.resource_action(resource_obj, action)

        # if dry_run:
        #     click.echo('EXECUTED:')
        #     for key in dry_run_executor.executed:
        #         click.echo('{}: {}'.format(
        #             click.style(dry_run_executor.compute_hash(key),
        #                         fg='green'),
        #                         str(key)
        #         ))


def init_cli_connect():
    @main.command()
    @click.argument('emitter')
    @click.argument('receiver')
    @click.argument('mapping', default='')
    def connect(mapping, receiver, emitter):
        mapping_parsed = None
        emitter = sresource.load(emitter)
        receiver = sresource.load(receiver)
        click.echo('Connect {} to {}'.format(emitter, receiver))

        if mapping:
            mapping_parsed = {}
            try:
                mapping_parsed.update(json.loads(mapping))
            except ValueError:
                for m in mapping.split():
                    k, v = m.split('->')
                    mapping_parsed.update({k: v})
        emitter.connect(receiver, mapping=mapping_parsed)

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
        emitter.disconnect(receiver)

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
    @click.option('--details', is_flag=True, default=False)
    def graph(start_with, end_with, details):
        g = signals.detailed_connection_graph(start_with=start_with,
                                              end_with=end_with,
                                              details=details)

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
    main.add_command(cli_repository)
    main.add_command(cli_inputs)
    main()


if __name__ == '__main__':
    run()
