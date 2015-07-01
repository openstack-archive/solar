
from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks


class LocalAnsible(object):

    def __init__(self, resources):
        self.resources = resources

    def action(self, resource, action):
        action_file = os.path.join(
            resource.metadata['actions_path'],
            resource.metadata['actions'][action])
        stats = callbacks.AggregateStats()
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

        play = PlayBook(
            playbook=action_file,
            host_list=['localhost'],
            extra_vars=resource.args_dict(),
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            transport='local')
        return play.run()
