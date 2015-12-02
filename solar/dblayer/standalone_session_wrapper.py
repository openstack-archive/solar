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

"""
Starts single seession, and ends it with `atexit`
can be used from cli / examples
shouldn't be used from long running processes (workers etc)

"""


def create_all():

    import sys
    if sys.executable.startswith(('python', )):
        # auto add session to only standalone python runs
        return

    from solar.dblayer.model import ModelMeta

    import atexit

    ModelMeta.session_start()

    atexit.register(ModelMeta.session_end)
