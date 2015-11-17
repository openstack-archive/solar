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

from solar.system_log import data
from solar.dblayer.solar_models import CommitedResource
from dictdiffer import patch
from solar.interfaces import orm
from solar.core.resource import resource
from .consts import CHANGES


def set_error(log_action, *args, **kwargs):
    sl = data.SL()
    item = next((i for i in sl if i.log_action == log_action), None)
    if item:
        resource_obj = resource.load(item.resource)
        resource_obj.set_error()
        item.state = 'error'
        item.save()


def move_to_commited(log_action, *args, **kwargs):
    sl = data.SL()
    item = next((i for i in sl if i.log_action == log_action), None)
    if item:
        resource_obj = resource.load(item.resource)
        commited = CommitedResource.get_or_create(item.resource)
        updated = resource_obj.db_obj.updated
        if item.action == CHANGES.remove.name:

            resource_obj.delete()
            commited.state = resource.RESOURCE_STATE.removed.name
        else:
            resource_obj.set_operational()
            commited.state = resource.RESOURCE_STATE.operational.name
            commited.base_path = item.base_path
            updated = resource_obj.db_obj.updated
            # required to update `updated` field
            resource_obj.db_obj.save()
        commited.inputs = patch(item.diff, commited.inputs)
        # TODO fix TagsWrp to return list
        # commited.tags = resource_obj.tags
        sorted_connections = sorted(commited.connections)
        commited.connections = patch(item.connections_diff, sorted_connections)
        commited.save()
        item.log = 'history'
        item.state = 'success'
        item.updated = updated
        item.save()
