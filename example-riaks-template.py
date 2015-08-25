from solar.core import template


nodes = template.nodes_from('templates/riak_nodes.yml')

riak_services = nodes.on_every(
    'resources/riak_node',
    {
        'riak_self_name': 'riak{num}',
        'riak_hostname': 'riak_server{num}.solar',
        'riak_name': 'riak{num}@riak_server{num}.solar',
})

riak_services.take(0).connect_list(
    riak_services.filter(
        lambda num: num > 0
    ),
    {
        'riak_name': 'join_to',
    }
)

hosts_files = nodes.on_every(
    'resources/hosts_file'
)

riak_services.connect_list_to_each(
    hosts_files,
    {
        'ip': 'hosts_ips',
        'riak_hostname': 'hosts_names',
    }
)
