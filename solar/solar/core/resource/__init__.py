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

__all__ = [
    'Resource',
    'create',
    'load',
    'load_all',
    'prepare_meta',
    'wrap_resource',
    'validate_resources',
]


from solar.core.resource.resource import Resource
from solar.core.resource.resource import load
from solar.core.resource.resource import load_all
from solar.core.resource.resource import wrap_resource
from solar.core.resource.virtual_resource import create
from solar.core.resource.virtual_resource import prepare_meta
from solar.core.resource.virtual_resource import validate_resources
