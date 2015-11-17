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

from celery import Celery

from solar.config import C

_url = 'redis://{}:{}/1'.format(C.redis.host, C.redis.port)

app = Celery(
    include=['solar.system_log.tasks', 'solar.orchestration.tasks'],
    backend=_url,
    broker=_url)
app.conf.update(CELERY_ACCEPT_CONTENT = ['json'])
app.conf.update(CELERY_TASK_SERIALIZER = 'json')
