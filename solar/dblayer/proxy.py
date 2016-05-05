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


import wrapt


class DBLayerProxy(wrapt.ObjectProxy):

    def __init__(self, wrapped):
        super(DBLayerProxy, self).__init__(wrapped)
        refs = wrapped._c.refs
        refs[wrapped.key][id(wrapped)] = wrapped

    def next(self, *args, **kwargs):
        return self.__wrapped__.next(*args, **kwargs)

    def __hash__(self):
        return hash(self.__wrapped__)

    def __eq__(self, other):
        if not isinstance(other, DBLayerProxy):
            return self.__wrapped__ == other
        return self.__wrapped__ == other.__wrapped__

    def __repr__(self):
        return "<P: %r>" % self.__wrapped__
