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
from solar.dblayer.model import ModelMeta
from solar.dblayer.solar_models import Resource


@fixture
def tagged_resources():
    base_tags = ['n1=x', 'n2']
    tags = base_tags + ['node=t1']
    t1 = Resource.from_dict('t1',
                            {'name': 't1', 'tags': tags, 'base_path': 'x'})
    t1.save_lazy()
    tags = base_tags + ['node=t2']
    t2 = Resource.from_dict('t2',
                            {'name': 't2', 'tags': tags, 'base_path': 'x'})
    t2.save_lazy()
    tags = base_tags + ['node=t3']
    t3 = Resource.from_dict('t3',
                            {'name': 't3', 'tags': tags, 'base_path': 'x'})
    t3.save_lazy()
    tags = ['node=t3']
    t4 = Resource.from_dict('t4',
                            {'name': 't4', 'tags': tags, 'base_path': 'x'})
    t4.save_lazy()
    ModelMeta.save_all_lazy()
    return [t1, t2, t3]


def test_add_remove_tags(tagged_resources):
    loaded = resource.load_by_tags({'n1', 'n2'})
    assert len(loaded) == 3

    for res in loaded:
        res.remove_tags('n1')

    assert len(resource.load_by_tags(set(['n1=']))) == 0
    assert len(resource.load_by_tags(set(['n2=']))) == 3


def test_filter_with_and(tagged_resources):
    loaded = resource.load_by_tags('node=t1 & n1=x')
    assert len(loaded) == 1
    loaded = resource.load_by_tags('node=t1,n1=*')
    assert len(loaded) == 1
    loaded = resource.load_by_tags('n2,n1=*')
    assert len(loaded) == 3
    loaded = resource.load_by_tags('node=* & n1=x')
    assert len(loaded) == 3


def test_filter_with_or(tagged_resources):
    loaded = resource.load_by_tags('node=t1 | node=t2')
    assert len(loaded) == 2
    loaded = resource.load_by_tags('node=t1 | node=t2 | node=t3')
    assert len(loaded) == 4


def test_with_brackets(tagged_resources):
    loaded = resource.load_by_tags('(node=t1 | node=t2 | node=t3) & n1=x')
    assert len(loaded) == 3
