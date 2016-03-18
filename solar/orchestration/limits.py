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


class Chain(object):

    def __init__(self, dg, inprogress, added):
        self.dg = dg
        self.inprogress = inprogress
        self.added = added
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    @property
    def filtered(self):
        for item in self.added:
            for rule in self.rules:
                if not rule(self.dg, self.inprogress, item):
                    break
            else:
                self.inprogress.append(item)
                yield item

    def __iter__(self):
        return iter(self.filtered)


def get_default_chain(dg, inprogress, added):
    chain = Chain(dg, inprogress, added)
    chain.add_rule(items_rule)
    chain.add_rule(target_based_rule)
    chain.add_rule(type_based_rule)
    return chain


def type_based_rule(dg, inprogress, item):
    """Checks type based rules

    condition should be specified like:
        type_limit: 2
    """
    if not item.type_limit:
        return True
    if not item.resource_type:
        return True

    type_count = 0
    for task in inprogress:
        if task.resource_type == item.resource_type:
            type_count += 1
    return item.type_limit > type_count


def target_based_rule(dg, inprogress, item, limit=1):
    if not item.target:
        return True

    target_count = 0
    for n in inprogress:
        if n.target == item.target:
            target_count += 1
    return limit > target_count


def items_rule(dg, inprogress, item, limit=100):
    return len(inprogress) < limit
