

from celery import Celery

app = Celery(
    include=['solar.system_log.tasks', 'solar.orchestration.tasks'],
    backend='redis://10.0.0.2:6379/1',
    broker='redis://10.0.0.2:6379/1')
app.conf.update(CELERY_ACCEPT_CONTENT = ['json'])
app.conf.update(CELERY_TASK_SERIALIZER = 'json')


# NOTE(dshulyak) some autodiscovery system
# maybe https://github.com/mitsuhiko/pluginbase/ ?
from solar.system_log.signals import *
from solar.system_log.tasks import *
from solar.orchestration.tasks import *

