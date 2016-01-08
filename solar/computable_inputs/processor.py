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

_av_processors = {}

from stevedore import driver
from threading import RLock


_processors = {}
_lock = RLock()


def get_processor(resource, input_name, computable_type, data, other=None):
    computable = resource.meta_inputs[input_name]['computable']
    lang = computable['lang']
    funct = computable['func']
    with _lock:
        if lang not in _processors:
            func = driver.DriverManager(namespace='solar.computable_inputs',
                                        name=lang,
                                        invoke_on_load=True).driver
            _processors[lang] = processor = func
        else:
            processor = _processors[lang]
    return processor.process(resource.name, computable_type, funct, data)
