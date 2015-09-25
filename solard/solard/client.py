import msgpack
import os

# TODO: handle errors

class SolardClient(object):

    read_buffer = 4096

    def __init__(self, auth, transport_args, transport_class=None):
        if transport_class is None:
            from solard.tcp_client import SolardTCPClient
            transport_class = SolardTCPClient
        self.auth = auth
        self.sudo_transport = transport_class(*transport_args)
        self.normal_transport = transport_class(*transport_args)
        self.make_auth()

    def make_auth(self):
        self.normal_transport.auth = dict(self.auth)
        self.sudo_transport.auth = dict(self.auth)
        self.sudo_transport.auth['sudo'] = True

    def run(self, *args, **kwargs):
        if kwargs.get('use_sudo'):
            transport = self.transport(use_sudo=True)
        else:
            transport = self.transport(use_sudo=False)
        send = transport.send({'m': 'run', 'args': args, 'kwargs': kwargs})
        resp = transport.resp()
        return resp

    def transport(self, use_sudo):
        if use_sudo:
            return self.sudo_transport
        return self.normal_transport

    def copy_directory(self, _from, _to, use_sudo=False):
        # dir should open context on remote, and sync all files as one req/resp
        to_cp_files = []
        transport = self.transport(use_sudo)
        for root, _, files in os.walk(_from):
            for name in files:
                _from = os.path.join(root, name)
                _to = os.path.join(root.replace(_from, _to), name)
                size = os.stat(_from).st_size
                to_cp_files.append((_from, _to, size))
        tos = [(x[1], size) for x in to_cp_files]
        total_size = sum((x[1] for x in tos))
        data = {'m': 'copy_files',
                'args': (tos, total_size),
                's': True}
        _ = transport.send(data)
        transport.send_stream_start()
        for _from, _to, _size in to_cp_files:
            # sock = transport.send_stream_cont(add_size=_size)
            sock = transport.send_stream_cont()
            with open(_from, 'rb') as f:
                while _size > 0:
                    data = f.read(self.read_buffer)
                    transport.send_stream_data(data)
                    _size -= len(data)
                assert _size == 0  # maybe somehow below ?
        transport.send_stream_end()
        resp = transport.resp()
        return resp

    def copy_file(self, _from, _to, use_sudo=False):
        transport = self.transport(use_sudo)
        f_size = os.stat(_from).st_size
        data = {'m': 'copy_file',
                'args': (_to, f_size),
                's': True}
        _ = transport.send(data)
        transport.send_stream_start(add_size=False)
        to_read = f_size
        with open(_from, 'rb') as f:
            while to_read > 0:
                data = f.read(self.read_buffer)  # expose sendfile there
                transport.send_stream_data(data)
                to_read -= len(data)
        assert to_read == 0
        transport.send_stream_end()
        return self.transport.resp()

    def copy(self, _from, _to, use_sudo=False):
        if os.path.isdir(_from):
            resp = self.copy_directory(_from, _to, use_sudo)
        else:
            resp = self.copy_file(_from, _to, use_sudo)
        return resp





if __name__ == '__main__':
    import time
    from solard.tcp_client import SolardTCPClient
    c = SolardClient(auth={'user': 'vagrant', 'auth': 'password'}, transport_args=('10.0.0.3', 5555), transport_class=SolardTCPClient)
    print c.run('hostname')
    print c.run('whoami')
    print c.run('whoami', use_sudo=True)
    print c.copy('/vagrant/library', '/tmp')
    # print c.copy('/tmp/a', '/tmp/bbb/b.%s' % (time.time()))
    # print c.copy('/tmp/bbb', '/tmp/s/ccc%s' % (time.time()))
