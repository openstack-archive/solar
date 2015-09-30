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

from pytest import fixture

from solar.core import resource


@fixture
def tagged_resources(resources):
    assert len(resources) == 3
    for res in resources.values():
        res.add_tags('n1', 'n2', 'n3')
    return resources


def test_add_remove_tags(tagged_resources):
    assert len(resource.load_by_tags({'n1', 'n2'})) == 3

    for res in tagged_resources.values():
        res.remove_tags('n1')

    assert len(resource.load_by_tags(set(['n1']))) == 0
    assert len(resource.load_by_tags(set(['n2']))) == 3
