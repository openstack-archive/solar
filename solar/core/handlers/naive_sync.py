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

from solar.core.handlers.base import BaseHandler


class NaiveSync(BaseHandler):

    def action(self, resource, action_name):
        # it is inconsistent with handlers because action_name
        # is totally useless piece of info here

        args = resource.args
        # this src seems not intuitive to me, wo context it is impossible
        # to understand where src comes from
        for item in args['sources']:
            self.transport_sync.copy(resource, item['src'], item['dst'])
            self.transport_sync.sync_all()
