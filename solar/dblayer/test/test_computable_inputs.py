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
from solar.dblayer.solar_models import InputTypes


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


def test_simple_lua_simple_max(rk):
    k1 = next(rk)
    k2 = next(rk)

    r1 = create_resource(k1, {'name': 'source1',
                              'inputs': {'input1': 10}})
    r2 = create_resource(k2, {'name': 'target1',
                              'inputs': {'input1': None}})

    r2.meta_inputs['input1']['computable'] = {'func': 'function(arr) return math.max(unpack(arr)) end',
                                              'lang': 'lua'}
    r1.connect(r2, {'input1': 'input1'})
    r1.save()
    r2.save()

    assert r2.inputs['input1'] == 10
