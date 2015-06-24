

import networkx as nx

import redis
import json

r = redis.StrictRedis(host='10.0.0.2', port=6379, db=1)


def save_graph(name, graph):
    # maybe it is possible to store part of information in AsyncResult backend
    r.set('{}:nodes'.format(name), json.dumps(graph.node.items()))
    r.set('{}:edges'.format(name), json.dumps(graph.edges(data=True)))


def get_graph(name):
    dg = nx.DiGraph()
    nodes = json.loads(r.get('{}:nodes'.format(name)))
    edges = json.loads(r.get('{}:edges'.format(name)))
    dg.add_nodes_from(nodes)
    dg.add_edges_from(edges)
    return dg
