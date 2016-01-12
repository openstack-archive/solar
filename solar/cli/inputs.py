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

import click
import yaml

from solar.core import resource as sresource
from solar.dblayer.model import NONE


@click.group(help="Manages raw resource inputs")
def inputs():
    pass


@inputs.command(help="Adds new input to resource")
@click.argument('resource')
@click.option("--name", '-n', help="Name of input")
@click.option("--value", '-v', help="Value input (yaml load will "
              " be executed on it)", default=NONE)
@click.option("--schema", '-s', help="Schema for input, "
              "will be guessed if not not given",
              default=None)
def add(resource, name, value, schema):
    r = sresource.load(resource)
    value = yaml.safe_load(value)
    r.input_add(name, value, schema)
    return


@inputs.command(help="Removes input from resource")
@click.argument('resource')
@click.option("--name", '-n', help="Name of input")
def remove(resource, name):
    r = sresource.load(resource)
    r.input_delete(name)
    pass


@inputs.command(help="Shows resource inputs metadata")
@click.argument('resource')
def show_meta(resource):
    r = sresource.load(resource)
    db_obj = r.db_obj
    meta = db_obj.meta_inputs
    click.echo(yaml.safe_dump(meta, default_flow_style=False))


@inputs.command(help="Allows change computable input properties")
@click.argument('resource')
@click.option("-n", '--name')
@click.option("-t", '--type', default=None)
@click.option("-f", '--func', default=None)
@click.option("-l", '--lang', default=None)
def change_computable(resource, name, func, type, lang):
    r = sresource.load(resource)
    r.input_computable_set(name, func, type, lang)
    return True


@inputs.command(help="Shows real input values, with full path")
@click.option('-v', '--values', default=False, is_flag=True)
@click.option('-r', '--real_values', default=False, is_flag=True)
@click.option('-i', '--input', default=None)
@click.argument('resource')
def backtrack(resource, input, values, real_values):
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
            click.echo('! Real value: %r\n' % sresource.load(
                resource).db_obj.inputs[name])
