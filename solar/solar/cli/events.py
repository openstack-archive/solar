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

import subprocess

import click
import networkx as nx

from solar.events import api as evapi


@click.group()
def events():
    pass


@events.command()
@click.argument('resource')
def show(resource):
    all_ = evapi.all_events(resource)
    if all_:
        click.echo('Resource: {}'.format(resource))
        offset = ' ' * 4
        for ev in all_:
            click.echo(offset+repr(ev))
    else:
        click.echo('No events for resource {}'.format(resource))


@events.command()
@click.argument('etype')
@click.argument('parent_node')
@click.argument('parent_action')
@click.argument('state')
@click.argument('depend_node')
@click.argument('depend_action')
def add(etype, parent_node, parent_action, state, depend_node, depend_action):
    ev = evapi.create_event(locals())
    evapi.add_event(ev)


@events.command()
@click.argument('etype')
@click.argument('parent_node')
@click.argument('parent_action')
@click.argument('state')
@click.argument('depend_node')
@click.argument('depend_action')
def rem(etype, parent_node, parent_action, state, depend_node, depend_action):
    ev = evapi.create_event(locals())
    evapi.remove_event(ev)


@events.command()
@click.argument('resource')
def trav(resource):
    dg = evapi.bft_events_graph(resource)
    nx.write_dot(dg, '{name}.dot'.format(name='events'))
    subprocess.call(
        'dot -Tpng {name}.dot -o {name}.png'.format(name='events'),
        shell=True)
