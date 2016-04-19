# -*- coding: utf-8 -*-
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from solar.core.handlers.ansible import complement_playbook


LEGACY = """- hosts: [{{host}}]
  sudo: yes
  tasks:
    - name: mariadb user
      mysql_user:
        name: {{ user_name }}
        password: {{ user_password }}"""

SIMPLE = """sudo: yes
tasks:
- name: mariadb user
  mysql_user:
    name: {{ user_name }}
    password: {{ user_password }}"""

SIMPLE_WITH_HEAD = """%YAML 1.2
---
sudo: yes
tasks:
- name: mariadb user
  mysql_user:
    name: {{ user_name }}
    password: {{ user_password }}"""

NO_LIST = """hosts: [{{host}}]
  sudo: yes
  tasks:
    - name: mariadb user
      mysql_user:
        name: {{ user_name }}
        password: {{ user_password }}"""

NO_HOST = """- sudo: yes
  tasks:
    - name: mariadb user
      mysql_user:
        name: {{ user_name }}
        password: {{ user_password }}"""


def test_legacy():
    """Ansible should not complement complete playbooks"""
    assert LEGACY == complement_playbook(LEGACY)


def test_simplest():
    """For playbooks that lack both list format and hosts the handler
    should complement both
    """
    assert '- hosts: [{{host}}]' in complement_playbook(SIMPLE)


def test_with_head():
    """Supllememtation whould work when YAML header is present"""
    assert '- hosts: [{{host}}]' in complement_playbook(SIMPLE_WITH_HEAD)


def test_nolist():
    """For playbooks that have list but no 'hosts' the 'hosts' should
    be complemented
    """
    assert '- hosts: [{{host}}]' in complement_playbook(NO_HOST)


def test_host():
    """Playbooks that have 'hosts',but no list should be transformed to
    lists. No additional hosts should be complemented
    """
    data = complement_playbook(NO_LIST)
    assert '- hosts: [{{host}}]' in data
    assert data.count('hosts') == 1
