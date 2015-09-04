
import subprocess

import networkx as nx

def write_graph(plan):
    """
    :param plan: networkx Graph object
    """
    colors = {
        'PENDING': 'cyan',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'INPROGRESS': 'yellow',
        'SKIPPED': 'blue'}

    for n in plan:
        color = colors[plan.node[n]['status']]
        plan.node[n]['color'] = color

    nx.write_dot(plan, '{name}.dot'.format(name=plan.graph['name']))
    subprocess.call(
        'tred {name}.dot | dot -Tpng -o {name}.png'.format(name=plan.graph['name']),
        shell=True)
