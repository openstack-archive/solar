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

    def run(self, transport):
        if self.valid:
            self._executor(transport)


class SyncTransport(object):
    """
    Transport that is responsible for file / directory syncing.
    """

    def __init__(self):
        self.executors = []

    def bind_with(self, other):
        # we migth add there something later
        # like compat checking etc
        self.other = other

    def copy(self, resource, *args, **kwargs):
        pass

    def preprocess(self, executor):
        # we can check there if we need to run sync executor or not
        # ideally would be to do so on other side
        # it may set executor.valid to False then executor will be skipped
        pass

    def preprocess_all(self):
        # we cat use there md5 for big files to check if we need to sync it
        #   or if remote is still valid
        # we can run that in parallell also
        # can be also used to prepare files for further transfer
        for executor in self.executors:
            self.preprocess(executor)

    def run_all(self):
        for executor in self.executors:
            executor.run(self)

    def sync_all(self):
        """
        It checks if action is required first,
        then runs all sequentially.
        Could be someday changed to parallel thing.
        """
        self.preprocess_all()
        self.run_all()
        self.executors = []  # clear after all


class RunTransport(object):
    """
    Transport that is responsible for executing remote commands, rpc like thing.
    """

    def __init__(self):
        pass

    def bind_with(self, other):
        # we migth add there something later
        # like compat checking etc
        self.other = other

    def run(self, resource, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
