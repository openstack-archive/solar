from hashlib import md5


class DryRunExecutor(object):
    def __init__(self, mapping=None):
        from fabric import api as fabric_api
        from fabric.contrib import project as fabric_project
        import mock

        from solar.core.handlers import puppet

        self.executed = []

        self.mapping = mapping or {}

        def dry_run_executor(command_name):
            def wrapper(*args, **kwargs):
                key = (len(self.executed), command_name, args, kwargs)

                self.executed.append(key)

                return self.find_hash(self.compute_hash(key))

            return wrapper

        # Add your own mocks here, IO, whatever
        fabric_api.local = mock.Mock(side_effect=dry_run_executor('LOCAL RUN'))
        fabric_api.put = mock.Mock(side_effect=dry_run_executor('PUT'))
        fabric_api.run = mock.Mock(side_effect=dry_run_executor('SSH RUN'))
        fabric_api.sudo = mock.Mock(side_effect=dry_run_executor('SSH SUDO'))
        fabric_project.rsync_project = mock.Mock(side_effect=dry_run_executor('RSYNC PROJECT'))

    def compute_hash(self, key):
        return md5(str(key)).hexdigest()

    def find_hash(self, hash):
        stripped_hashes = {k.replace('>', ''): k for k in self.mapping}

        hashes = [k for k in stripped_hashes if hash.startswith(k)]

        if len(hashes) == 0:
            #raise Exception('Hash {} not found'.format(hash))
            return ''
        elif len(hashes) > 1:
            raise Exception('Hash {} not unique in {}'.format(
                hash, hashes
            ))

        hash = stripped_hashes[hashes[0]]

        if hash.endswith('>'):
            with open(self.mapping[hash]) as f:
                return f.read()

        return self.mapping[hash]
