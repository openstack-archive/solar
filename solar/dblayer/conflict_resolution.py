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

from collections import Counter


def naive_resolver(riak_object):
    # for now we support deleted vs existing object
    siblings = riak_object.siblings
    siblings_len = map(
        lambda sibling: (len(sibling._get_encoded_data()), sibling), siblings)
    siblings_len.sort()
    c = Counter((x[0] for x in siblings_len))
    if len(c) > 2:
        raise RuntimeError(
            "Too many different siblings, not sure what to do with siblings")
    if 0 not in c:
        raise RuntimeError("No empty object for resolution"
                           " not sure what to do with siblings")
    selected = max(siblings_len)
    # TODO: pass info to obj save_lazy too
    riak_object.siblings = [selected[1]]


dblayer_conflict_resolver = naive_resolver
