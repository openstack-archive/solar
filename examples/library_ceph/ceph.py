
from solar.core.resource import virtual_resource as vr
from solar.interfaces.db import get_db

import yaml

db = get_db()

STORAGE = {'objects_ceph': True,
           'osd_pool_size': 2,
           'pg_num': 128}

KEYSTONE = {'admin_token': 'abcde'}


NETWORK_SCHEMA = {
    'endpoints': {'eth1': {'IP': ['10.0.0.3/24']}},
    'roles': {'ceph/replication': 'eth1',
              'ceph/public': 'eth1'}
    }

NETWORK_METADATA = yaml.load("""
    solar-dev1:
      uid: '1'
      fqdn: solar-dev1
      network_roles:
        ceph/public: 10.0.0.3
        ceph/replication: 10.0.0.3
      node_roles:
        - ceph-mon
      name: solar-dev1

    """)


def deploy():
    db.clear()
    resources = vr.create('nodes', 'templates/nodes.yaml', {'count': 1})
    first_node = next(x for x in resources if x.name.startswith('node'))

    library = vr.create('library1', 'resources/fuel_library', {})[0]
    first_node.connect(library)

    keys = vr.create('ceph_key', 'resources/ceph_keys', {})[0]
    first_node.connect(keys)
    # TODO(use library resource)
    # ceph_mon = vr.create('ceph_mon1', 'resources/ceph_mon',
    #     {'storage': STORAGE,
    #      'keystone': KEYSTONE,
    #      'network_scheme': NETWORK_SCHEMA,
    #      'ceph_monitor_nodes': NETWORK_METADATA,
    #      'ceph_primary_monitor_node': NETWORK_METADATA,
    #      'role': 'controller',
    #      })[0]
    # first_node.connect(ceph_mon,
    #     {'ip': ['ip', 'public_vip', 'management_vip']})


if __name__ == '__main__':
    deploy()
