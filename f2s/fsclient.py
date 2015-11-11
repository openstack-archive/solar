#!/usr/bin/env python


import click

@click.group()
def main():
    pass

@click.command()
@click.parameter('nodes', nargs=-1)
def nodes(nodes):
    from fuelclient.objects.node import Node
    nodes_obj = map(Node, nodes)

