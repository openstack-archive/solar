.. _handler_ansible_details:

Ansible Handler
===============

Let's look into simple ``hosts_file/actions/run.yaml`` example ::

  - hosts: [{{host}}]
    sudo: yes
    tasks:
      {% for val in hosts %}
      - name: Create hosts entries for {{val['name']}} => {{val['ip']}}
        lineinfile:
          dest: /etc/hosts
          regexp: ".*{{val['name']}}$"
          line: "{{val['ip']}} {{val['name']}}"
          state: present
      {% endfor %}

It's pretty much standard ansible playbook, but it is processed with jinja2 before ansible is executed.

Solar will create proper inventory ::

  localhost ansible_connection=local user=vagrant location_id="d6255f99dda2fca55177ffad96f390a9" transports_id="2db90247d5d94732448ebc5fdcc9f80d" hosts="[{'ip': u'10.0.0.4', 'name': u'node1'}, {'ip': u'10.0.0.3', 'name': u'node0'}]"

Playbook will be also created ::

  - hosts: [localhost]
    sudo: yes
    tasks:

      - name: Create hosts entries for node1 => 10.0.0.4
        lineinfile:
          dest: /etc/hosts
          regexp: ".*node1$"
          line: "10.0.0.4 node1"
          state: present

      - name: Create hosts entries for node0 => 10.0.0.3
        lineinfile:
          dest: /etc/hosts
          regexp: ".*node0$"
          line: "10.0.0.3 node0"
          state: present

You may wonder about ``hosts: [{{host}}]``, we have our own :ref:`res-transports-term` so we execute ansible like this ::

  ansible-playbook --module-path /tmp/library -i /tmp/tmpkV0U5F/tmpGmLGEwhosts_file2/inventory /tmp/tmpkV0U5F/tmpGmLGEwhosts_file2/runlNjnI3
