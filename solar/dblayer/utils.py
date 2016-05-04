#    Copyright 2016 Mirantis, Inc.
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

from solar.dblayer.model import DBLayerException
from solar.dblayer import ModelMeta


class Atomic(object):

    def __enter__(self):
        lazy_saved = ModelMeta.find_non_empty_lazy_saved()
        if lazy_saved:
            raise DBLayerException(
                'Some objects could be accidentally rolled back on failure, '
                'Please ensure that atomic helper is initiated '
                'before any object is saved. '
                'See list of objects: %r', lazy_saved)
        ModelMeta.session_start()

    def __exit__(self, *exc_info):
        # if there was an exception - rollback immediatly,
        # else catch any during save - and rollback in case of failure
        try:
            ModelMeta.session_end(result=not any(exc_info))
        except Exception:
            ModelMeta.session_end(result=False)


@wrapt.decorator
def atomic(wrapped, instance, args, kwargs):
    with Atomic():
        return wrapped(*args, **kwargs)
