from solar import template


nodes = template.nodes_from('templates/riak_nodes.yml')

riak_services = nodes.on_each(
    'resources/riak_node',
    {
        'riak_self_name': 'riak{num}',
        'riak_hostname': 'riak_server{num}.solar',
        'riak_name': 'riak{num}@riak_server{num}.solar',
})

slave_riak_services = riak_services.filter(lambda num: num > 0)

riak_services.take(0).connect_list(
    slave_riak_services,
    {
        'riak_name': 'join_to',
    }
)

hosts_files = nodes.on_each('resources/hosts_file')

riak_services.connect_list_to_each(
    hosts_files,
    {
        'ip': 'hosts_ips',
        'riak_hostname': 'hosts_names',
    }
)


hosts_files.add_deps('run/success', riak_services, 'run')
slave_riak_services.add_reacts('run/success', slave_riak_services, 'join')
slave_riak_services.add_reacts('leave/success', slave_riak_services, 'join')
slave_riak_services.add_react('run/success', riak_services.take(0), 'commit')
