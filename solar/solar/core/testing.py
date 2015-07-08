import imp
import networkx as nx
import os

from solar.core import resource
from solar.core import signals


def test_all():
    conn_graph = signals.detailed_connection_graph()
    #srt = nx.topological_sort(conn_graph)

    for name in conn_graph:
        print 'Trying {}'.format(name)
        r = resource.load(name)

        script_path = os.path.join(r.metadata['base_path'], 'test.py')
        if not os.path.exists(script_path):
            print 'WARNING: resource {} has no tests'.format(name)
            continue

        print 'File {} found'.format(script_path)

        with open(script_path) as f:
            module = imp.load_module(
                '{}_test'.format(name),
                f,
                script_path,
                ('', 'r', imp.PY_SOURCE)
            )

        module.test(r)
