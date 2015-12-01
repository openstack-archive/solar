import click
import sys
import time

from solar.core import signals
from solar.core.resource import virtual_resource as vr
from solar.dblayer.model import ModelMeta


def run():
    ModelMeta.remove_all()

    resources = vr.create('nodes', 'templates/nodes.yaml', {'count': 2})


run()
