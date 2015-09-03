import imp
import os
import traceback

from log import log
from solar.core import resource
from solar.core import signals


def test_all():
    results = {}

    conn_graph = signals.detailed_connection_graph()
    #srt = nx.topological_sort(conn_graph)

    for name in conn_graph:
        log.debug('Trying {}'.format(name))
        r = resource.load(name)

        script_path = os.path.join(r.metadata['base_path'], 'test.py')
        if not os.path.exists(script_path):
            log.warning('resource {} has no tests'.format(name))
            continue

        log.debug('File {} found'.format(script_path))

        with open(script_path) as f:
            module = imp.load_module(
                '{}_test'.format(name),
                f,
                script_path,
                ('', 'r', imp.PY_SOURCE)
            )

        try:
            module.test(r)
            results[name] = {
                'status': 'ok',
            }
        except:
            results[name] = {
                'status': 'error',
                'message': traceback.format_exc(),
            }

    return results
