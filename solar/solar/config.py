
import os

class DictWrp(object):

    def __init__(self, store):
        self.store = store

    def __getitem__(self, item):
        return self.store[item]

    __getattr__ = __getitem__


class Conf(object):

    def __init__(self):
        self.store = {}
        self.types = {}

    def add(self, name, _type=None, default=None):
        if default:
            if hasattr(default, '__call__'):
                val = default()
            else:
                val = default
            _type = type(val)
        self.types[name] = _type
        if '.' in name:
            parent, child = name.split('.')
            if parent not in self.store:
                self.store[parent] = {}
                self.types[parent] = dict
            self.store[parent][child] = val
        else:
            self.store[name] = val

    def __getitem__(self, item):
        val = self.store[item]
        if isinstance(val, dict):
            return DictWrp(val)
        return val

    def __setitem__(self, item, val):
        stack = item.split('.')
        while stack[:-1]:
            nxt = stack.pop(0)
            store = self.store[nxt]
        store[stack[-1]] = val

    def init_env(self):
        for var, _type in self.types.iteritems():
            if '.' in var:
                variable = '_'.join(var.split('.'))
            else:
                variable = var
            env_var = variable.upper()
            val = os.getenv(env_var)
            if not val: continue

            if _type == list:
                val_lst = val.split('|')
                self.store[var].extend(val_lst)
            elif _type == dict:
                pass
            else:
                self.store[var] = val



    __getattr__ = __getitem__


C = Conf()
C.add('redis.port', default='6379')
C.add('redis.host', default='10.0.0.2')
C.add('riak.host', default='10.0.0.2')
C.add('riak.port', default='8087')
C.add('riak.protocol', default='pbc')
C.init_env()

if __name__ == '__main__':
    print C.store
