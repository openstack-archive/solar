import os
import random
import string
from contextlib import nested
from fabric import api as fabric_api
from subprocess import check_output
import shlex
from itertools import takewhile



# XXX: not used for now vvv

# def common_path(paths, sep=os.path.sep):
#     paths = [x.split(sep) for x in paths]
#     dirs = zip(*(p for p in paths))
#     return [x[0] for x in takewhile(lambda x: all(n == x[0] for n in x[1:]), dirs)]


# class SolardContext(object):

#     def __init__(self):
#         self._dirs = {}
#         self._files = {}

#     def file(self, path):
#         try:
#             return self._files[path]
#         except KeyError:
#             if self.is_safe_file(path):
#                 cls = SolardSafeFile
#             else:
#                 cls = SolardFile
#             self._files[path] = f = cls(self, path)
#         return f

#     def dir(self, path):
#         try:
#             return self._dirs[path]
#         except KeyError:
#             self._dirs[path] = solard_dir = SolardDir(self, path)
#         return solard_dir

#     def is_safe_file(self, path):
#         dirname = os.path.dirname(path)
#         common = SolardContext.common_path(dirname, self._dirs.keys())
#         if common not in ((), ('/', )):
#             return False
#         return True

#     def is_safe_dir(self, path):
#         common = SolardContext.common_path(path, self._dirs.keys())
#         if common not in ((), ('/', )):
#             return False
#         return True

#     @staticmethod
#     def common_path(path, paths, sep=os.path.sep):
#         all_paths = paths + [path]
#         paths = [x.split(sep) for x in all_paths]
#         dirs = zip(*(p for p in all_paths))
#         return tuple(x[0] for x in takewhile(lambda x: all(n == x[0] for n in x[1:]), dirs))


# class SolardSafeFile(object):

#     def __init__(self, context, target):
#         self._f = None
#         self._rnd = 'solar' + ''.join((random.choice(string.ascii_lowercase) for _ in xrange(6)))
#         self._path = target
#         self._safe_path = self._path + '_' + self._rnd

#     def open(self):
#         self._f = open(self._safe_path, 'wb')

#     def write(self, data):
#         return self._f.write(data)

#     def close(self):
#         self._f.close()

#     def finish(self):
#         self.close()
#         os.rename(self._safe_path, self._path)


# class SolardFile(object):

#     def __init__(self, context, target):
#         self._f = None
#         self._path = target

#     def open(self):
#         self._f = open(self._path, 'wb')

#     def write(self, data):
#         self._f.write(data)

#     def close(self):
#         self._f.close()

#     def finish(self):
#         self.close()


# class SolardSafeDir(object):

#     def __init__(self, context, target):
#         self._rnd = 'solar' + ''.join((random.choice(string.ascii_lowercase) for _ in xrange(6)))
#         self._path = target
#         self._safe_path = self._path + '_' + self._rnd

#     def start(self):
#         os.makedirs(self._safe_path)

#     def finish(self):
#         os.rename(self._safe_path, self._path)


# class SolardDir(object):

#     def __init__(self, context, target):
#         self._path = target

#     def start(self):
#         os.makedirs(self._path)

#     def finish(self):
#         pass

# XXX: not used for now ^^^

class SolardContext(object):

    def __init__(self):
        self.files = {}

    def file(self, path):
        try:
            return self.files[path]
        except KeyError:
            self.files[path] = r = SolardFile(self, path)
        return r


class SolardFile(object):

    def __init__(self, context, target):
        self.ctx = context
        self._rnd = 'solar' + ''.join((random.choice(string.ascii_lowercase) for _ in xrange(6)))
        self._path = target
        self._f = None
        self._safe_path = self._path + '_' + self._rnd

    def open(self):
        dirname = os.path.dirname(self._safe_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if self._f is None:
            self._f = open(self._safe_path, 'wb')

    def write(self, data):
        self._f.write(data)

    def finish(self):
        self._f.close()
        self._f = None
        os.rename(self._safe_path, self._path)


class SolardIface(object):

    @staticmethod
    def run(solard_context, cmd, **kwargs):
        # return check_output(shlex.split(cmd))
        executor = fabric_api.local
        if kwargs.get('use_sudo', False):
            cmd = 'sudo ' + cmd

        managers = []

        cwd = kwargs.get('cwd')
        if cwd:
            managers.append(fabric_api.cd(kwargs['cwd']))

        env = kwargs.get('env')
        if env:
            managers.append(fabric_api.shell_env(**kwargs['env']))

        if kwargs.get('warn_only', False):
            managers.append(fabric_api.warn_only())

        with nested(*managers):
            out = executor(cmd, capture=True)
            if out.failed:
                raise Exception("Remote failed")
            return out.stdout

    @staticmethod
    def copy_file(solard_context, stream_reader, path, size=None):
        f = SolardIface.file_start(solard_context, path)
        rdr = stream_reader(size)
        for data in rdr:
            f.write(data)
        SolardIface.file_end(solard_context, path)
        return True

    # # TODO: not used YET fully
    # @staticmethod
    # def dir_start(solard_context, path):
    #     solard_dir = solard_context.dir(path)
    #     solard_dir.start()
    #     return solard_dir

    # @staticmethod
    # def dir_finish(solard_context, path):
    #     solard_dir = solard_context.dir(path)
    #     solard_dir.finish()
    #     return True

    @staticmethod
    def file_start(solard_context, path):
        solard_file = solard_context.file(path)
        solard_file.open()
        return solard_file

    @staticmethod
    def file_put_data(solard_context, path, data):
        solard_file = solard_context.file(path)
        return solard_file.write(data)

    @staticmethod
    def file_end(solard_context, path):
        solard_file = solard_context.file(path)
        solard_file.finish()
        return True

