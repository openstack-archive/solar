class Executor(object):

    def __init__(self, resource, executor, params=None):
        """
        :param resource: solar resource
        :param executor: callable executor, that will perform action
        :param params: optional argument
                       that migth be used later for decomposition etc
        """
        self.resource = resource
        self.params = params
        self._executor = executor
        self._valid = True

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        self._valid = value

    def run(self):
        self._executor()


class SyncTransport(object):
    """
    Transport that is responsible for file / directory syncing.
    """

    def __init__(self):
        self.executors = []

    def copy(self, resource, *args, **kwargs):
        pass

    def check(self, executor):
        # we can check there if we need to run sync executor or not
        # ideally would be to do so on other side
        # it may set executor.valid to False then executor will be skipped
        pass

    def _check_all(self):
        # we cat use there md5 for big files to check if we need to sync it
        #   or if remote is still valid
        # we can run that in parallell also
        for executor in self.executors:
            self.check(executor)

    def _run_all(self):
        for executor in self.executors:
            if executor.valid:
                executor.run()

    def sync_all(self):
        """
        It checks if action is required first,
        then runs all sequentially.
        Could be someday changed to parallel thing.
        """
        self._check_all()
        self._run_all()
        self.executors = []  # clear after all


class RunTransport(object):
    """
    Transport that is responsible for executing remote commands, rpc like thing.
    """

    def __init__(self):
        pass

    def run(self, resource, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
