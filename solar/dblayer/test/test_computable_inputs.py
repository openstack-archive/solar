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

from __future__ import print_function

import pytest

from solar.dblayer.test.test_real import create_resource
from solar.computable_inputs import ComputablePassedTypes as CPT


dth = pytest.dicts_to_hashable


def test_simple_noop(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})

    r2.meta_inputs['input1']['computable'] = {'func': None,
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r1.save()
    r2.save()

    assert r2.inputs['input1'] == [10]


def test_full_noop(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})

    r2.meta_inputs['input1']['computable'] = {'func': None,
                                              'type': CPT.full.name,
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r1.save()
    r2.save()

    assert r2.inputs['input1'] == [{'value': 10, 'resource': r1.key,
                                    'other_input': 'input1'}]


def test_simple_lua_simple_max(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r3 = create_resource(k3, {'name': 'source1',
                              'inputs': {'input1': 11}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})

    lua_funct = 'function(arr) return math.max(unpack(arr)) end'
    r2.meta_inputs['input1']['computable'] = {'func': lua_funct,
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r3.connect(r2, {'input1': 'input1'})

    r1.save()
    r2.save()
    r3.save()

    assert r2.inputs['input1'] == 11


def test_full_lua_array(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r3 = create_resource(k3, {'name': 'source1',
                              'inputs': {'input1': 11}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})

    # raw python object, counts from 0
    lua_funct = 'function(arr) return arr end'
    r2.meta_inputs['input1']['computable'] = {'func': lua_funct,
                                              'type': CPT.full.name,
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r3.connect(r2, {'input1': 'input1'})

    r1.save()
    r2.save()
    r3.save()

    res_inputs = set(dth(r2.inputs['input1']))
    comparsion = set(dth([{'value': 11, 'resource': r3.key,
                           'other_input': 'input1'},
                          {'value': 10, 'resource': r1.key,
                           'other_input': 'input1'}]))
    assert res_inputs == comparsion


def test_connect_to_computed(rk):
    k1 = next(rk)
    k2 = next(rk)
    k3 = next(rk)
    k4 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r3 = create_resource(k3, {'name': 'source1',
                              'inputs': {'input1': 11}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})
    r4 = create_resource(k4, {'name': 'target1',
                              'inputs': {'input1': None}})

    lua_funct = 'function(arr) return math.max(unpack(arr)) end'
    r2.meta_inputs['input1']['computable'] = {'func': lua_funct,
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r3.connect(r2, {'input1': 'input1'})

    r2.connect(r4, {'input1': 'input1'})

    r1.save()
    r2.save()
    r3.save()
    r4.save()

    assert r4.inputs['input1'] == 11

