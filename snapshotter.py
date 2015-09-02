import click
import time
from itertools import takewhile
from subprocess import check_output


def get_vagrant_vms():
    status = vagrant('status')
    lines = status.splitlines()[2:]
    vms = takewhile(lambda x: x.split(), lines)
    vms = map(lambda x: x.split()[0], vms)
    return vms


def vboxmanage(*args):
    args = ('VBoxManage', ) + args
    p = check_output(args, shell=False)
    return p


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
    if n is None:
        n = 'solar-%d' % time.time()
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo("Taking", vm)
        snap = vboxmanage('snapshot', vm, 'take', n, '--live')
        click.echo(snap)


@click.option('-n')
@cli.command()
def restore(n):
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo("Restoring", vm)
        snap = vboxmanage('snapshot', vm, 'restore', n)
        click.echo(snap)


# wanted to use list but it would
@cli.command()
def show():
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo("VM: %s" % vm)
        snap = vboxmanage('snapshot', vm, 'list')
        click.echo(snap)
        click.echo('-' * 10)


@click.option('-n')
@cli.command()
def delete(n):
    vms = get_vagrant_vms()
    for vm in vms:
        click.echo('Removing %s from %s' % (n, vm))
        snap = vboxmanage('snapshot', vm, 'delete', n)
        click.echo(snap)


if __name__ == '__main__':
    cli()
