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

import json
import os
import sys

import click
import tabulate
import yaml

from solar.cli import executors
from solar.core import actions
from solar.core.log import log
from solar.core import resource as sresource
from solar.core.resource import virtual_resource as vr
from solar import errors
from solar import utils


@click.group()
def resource():
    pass


@resource.command()
@click.argument('action')
@click.argument('resource')
@click.option('-d', '--dry-run', default=False, is_flag=True)
@click.option('-m', '--dry-run-mapping', default='{}')
def action(dry_run_mapping, dry_run, action, resource):
    if dry_run:
        dry_run_executor = executors.DryRunExecutor(
            mapping=json.loads(dry_run_mapping))

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
@click.option('-v', '--values', default=False, is_flag=True)
@click.option('-r', '--real_values', default=False, is_flag=True)
@click.option('-i', '--input', default=None)
@click.argument('resource')
def backtrack_inputs(resource, input, values, real_values):
    r = sresource.load(resource)

    db_obj = r.db_obj

    def single(resource, name, get_val=False):
        db_obj = sresource.load(resource).db_obj
        se = db_obj.inputs._single_edge(name)
        se = tuple(se)
        if not se:
            if get_val:
                return dict(resource=resource,
                            name=name,
                            value=db_obj.inputs[name])
            else:
                return dict(resource=resource, name=name)
        l = []
        for (rname, rinput), _, meta in se:
            l.append(dict(resource=resource, name=name))
            val = single(rname, rinput, get_val)
            if meta and isinstance(val, dict):
                val['meta'] = meta
            l.append(val)
        return l

    inps = {}
    if input:
        inps[input] = single(resource, input, values)
    else:
        for _inp in db_obj.inputs:
            inps[_inp] = single(resource, _inp, values)

    for name, values in inps.iteritems():
        click.echo(yaml.safe_dump({name: values}, default_flow_style=False))
        if real_values:
            click.echo('! Real value: %r' % sresource.load(
                resource).db_obj.inputs[name], nl=True)


@resource.command()
def compile_all():
    from solar.core.resource import compiler

    destination_path = utils.read_config()['resources-compiled-file']

    if os.path.exists(destination_path):
        os.remove(destination_path)

    resources_files_mask = utils.read_config()['resources-files-mask']
    for path in utils.find_by_mask(resources_files_mask):
        meta = utils.yaml_load(path)
        meta['base_path'] = os.path.dirname(path)

        compiler.compile(meta)


@resource.command()
def clear_all():
    from solar.dblayer.model import ModelMeta
    click.echo('Clearing all resources and connections')
    ModelMeta.remove_all()


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
    resources = vr.create(name, base_path, args=args_parsed)
    for res in resources:
        click.echo(res.color_repr())


@resource.command()
@click.option('--name', '-n', default=None)
@click.option('--tag', '-t', multiple=True)
@click.option('--as_json', default=False, is_flag=True)
@click.option('--color', default=True, is_flag=True)
def show(name, tag, as_json, color):
    echo = click.echo_via_pager
    if name:
        resources = [sresource.load(name)]
        echo = click.echo
    elif tag:
        resources = sresource.load_by_tags(set(tag))
    else:
        resources = sresource.load_all()

    if as_json:
        output = json.dumps([r.to_dict(inputs=True)
                             for r in resources], indent=2)
        echo = click.echo
    else:
        if color:
            formatter = lambda r: r.color_repr(inputs=True)
        else:
            formatter = lambda r: unicode(r)
        output = '\n'.join(formatter(r) for r in resources)

    if output:
        echo(output)


@resource.command()
@click.argument('resource_name')
@click.argument('tags', nargs=-1)
@click.option('--add/--delete', default=True)
def tag(add, tags, resource_name):
    r = sresource.load(resource_name)
    if add:
        r.add_tags(*tags)
        click.echo('Tag(s) {} added to {}'.format(tags, resource_name))
    else:
        r.remove_tags(*tags)
        click.echo('Tag(s) {} removed from {}'.format(tags, resource_name))


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
    errors = sresource.validate_resources()
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
    click.echo(vr.get_inputs(content))


@resource.command()
@click.option('--name', '-n', default=None)
@click.option('--tag', '-t', multiple=True)
@click.option('-f', default=False, is_flag=True,
              help='force removal from database')
def remove(name, tag, f):
    if name:
        resources = [sresource.load(name)]
    elif tag:
        resources = sresource.load_by_tags(set(tag))
    else:
        resources = sresource.load_all()
    for res in resources:
        res.remove(force=f)
        if f:
            msg = 'Resource %s removed from database' % res.name
        else:
            msg = 'Resource %s will be removed after commiting changes.'
            msg = msg % res.name
        click.echo(msg)
