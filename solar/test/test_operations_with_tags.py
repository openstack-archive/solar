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
from solar.dblayer.solar_models import Resource
from solar.dblayer.model import ModelMeta


@fixture
def tagged_resources():
    tags = ['n1', 'n2', 'n3']
    t1 = Resource.from_dict('t1',
        {'name': 't1', 'tags': tags, 'base_path': 'x'})
    t1.save_lazy()
    t2 = Resource.from_dict('t2',
        {'name': 't2', 'tags': tags, 'base_path': 'x'})
    t2.save_lazy()
    t3 = Resource.from_dict('t3',
        {'name': 't3', 'tags': tags, 'base_path': 'x'})
    t3.save_lazy()
    ModelMeta.save_all_lazy()
    return [t1, t2, t3]


def test_add_remove_tags(tagged_resources):
    loaded = resource.load_by_tags({'n1', 'n2'})
    assert len(loaded) == 3

    for res in loaded:
        res.remove_tags('n1')

    assert len(resource.load_by_tags(set(['n1']))) == 0
    assert len(resource.load_by_tags(set(['n2']))) == 3
