
How to approach primary, non-primary resource mangement?
--------------------------------------------------------

It should be possible to avoid storing primary/non-primary flag
for any particular resource.

In ansible there is a way to execute particular task from playbook
only once and on concrete host.

::
    - hosts: [mariadb]
      tasks:
        - debug: msg="Installing first node"
          run_once: true
          delegate_to: groups['mariadb'][0]
        - debug: msg="Installing all other mariadb nodes"
          when: inventory_hostname != groups['mariadb'][0]
