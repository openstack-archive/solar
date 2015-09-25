#!/usr/bin/env python
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
import time
from itertools import takewhile
from subprocess import check_output, CalledProcessError


def get_vagrant_vms():
    status = vagrant('status')
    lines = status.splitlines()[2:]
    vms = takewhile(lambda x: x.split(), lines)
    vms = map(lambda x: x.split()[0], vms)
    return vms


def vboxmanage(args, output_dict=False):
    args = ['VBoxManage'] + args
    if output_dict:
        args = args + ['--machinereadable']
    p = check_output(args, shell=False)
    if not output_dict:
        return p

    elements = [line.split('=') for line in p.split('\n') if line]

    return {
        el[0]: el[1].strip('""')
        for el in elements if el
    }


def vagrant(*args):
    args = ('vagrant', ) + args
    p = check_output(args, shell=False)
    return p


@click.group()
def cli():
    pass


@cli.command()
@click.option('-n', default=None)
def take(n):
    now = time.time()
    if n is None:
        n = 'solar-%d' % now
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo("Taking %s" % vm)
        snap = vboxmanage(['snapshot', vm, 'take', n, '--live', '--description', 'solar: %d' % now])
        click.echo(snap)


@click.option('-n', required=True)
@cli.command()
def restore(n):
    vms = get_vagrant_vms()
    for vm in vms:
        vminfo = vboxmanage(['showvminfo', vm], output_dict=True)
        was_running = False
        if vminfo['VMState'] == 'running':
            click.echo('[{vm}] Running, stopping'.format(vm=vm))
            vboxmanage(['controlvm', vm, 'poweroff'])
            was_running = True
        click.echo("Restoring %s" % vm)
        snap = vboxmanage(['snapshot', vm, 'restore', n])
        if was_running:
            vboxmanage(['startvm', vm, '--type', 'headless'])
        click.echo(snap)


# wanted to use list but it would
@cli.command()
def show():
    vms = get_vagrant_vms()
    for vm in vms:
        msg = "[{vm}] {snap}"
        click.echo(click.style(vm, fg='green'))
        try:
            snap = vboxmanage(['snapshot', vm, 'list'], output_dict=True)
            snap_num = (len(snap.keys()) / 3) - 1
            if snap_num < 1:
                click.echo(click.style(
                    'This machine does not have any snapshots',
                    fg='red'
                ))
            else:
                s = {}
                for key, value in snap.items():
                    if not key.startswith('SnapshotName'):
                        continue
                    uuid_key = key.replace("SnapshotName", "SnapshotUUID")
                    click.echo('\t{name} (UUID {uuid})'.format(name=value, uuid=snap[uuid_key]))
        except CalledProcessError:
            click.echo(click.style(
                'This machine does not have any snapshots',
                fg='red'
            ))
        click.echo('-' * 10)


@click.option('-n')
@cli.command()
def delete(n):
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo('Removing %s from %s' % (n, vm))
        snap = vboxmanage(['snapshot', vm, 'delete', n])
        click.echo(snap)


if __name__ == '__main__':
    cli()
