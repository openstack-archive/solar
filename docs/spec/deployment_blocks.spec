

Profile is a global wrapper for all resources in environment.
Profile is versioned and executed by particular driver.
Profile is a container for resources.
Resources can be grouped by roles entities.

::

    id: HA
    type: profile
    version: 0.1
    # adapter for any application that satisfies our requirements
    driver: ansible


Role is a logical wrapper of resources.
We will provide "opinionated" wrappers, but user should
be able to compose resource in any way.

::

    roles:
        - id: controller
          type: role
          resources: []


Resource should have deployment logic for several events:
main deployment, removal of resource, scale up of resource ?
Resource should have list of input parameters that resource provides.
Resources are isolated, and should be executable as long as
required data provided.

::
    id: rabbitmq
    type: resource
    driver: ansible_playbook
    actions:
        run: $install_rabbitmq_playbook
    input:
        image: fuel/rabbitmq
        port: 5572
        # we need to be able to select ip addresses
        listen: [{{management.ip}}, {{public.ip}}]


::
    id: nova_compute
    type: resource
    driver: ansible_playbook
    actions:
        run: $link_to_ansible_playbook
        remove: $link_to_another_playbook_that_will_migrate_vms
        maintenance: $link_to_playbook_that_will_put_into_maintenance
    input:
        image: fuel/compute
        driver: kvm
        rabbitmq_hosts: []

