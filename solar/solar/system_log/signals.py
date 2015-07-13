
from celery.signals import task_failure, task_success

from solar.system_log import operations
from solar.system_log import tasks


__all__ = ['system_log_on_task_error', 'system_log_on_task_success']


@task_failure.connect
def system_log_on_task_error(sender, exception, traceback, einfo, *args, **kwargs):
    task_id = kwargs.get('task_id')
    if task_id:
        tasks.error_logitem.apply_async(args=[task_id], queue='system_log')

@task_success.connect
def system_log_on_task_success(sender, result, *args, **kwargs):
    task_id = kwargs.get('task_id')
    if task_id:
        tasks.commit_logitem.apply_async(args=[task_id], queue='system_log')
