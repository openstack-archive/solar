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

from solar.orchestration.workers import base


class SubTest(base.Worker):
    """for tests."""

    def pass_two(self, ctxt):
        return 2


def test_subscribe_on_success():
    sub = SubTest()
    test = []
    assert sub.pass_two.on_success(lambda ctxt, rst: test.append(rst)) is None
    assert sub.pass_two({}) == 2
    assert test == [2]


def test_subscribe_for_all():
    sub = SubTest()
    test = []
    sub.for_all.after(lambda ctxt: test.append('after'))
    sub.for_all.before(lambda ctxt: test.append('before'))
    sub.pass_two({})
    assert test == ['before', 'after']
