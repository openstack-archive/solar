import msgpack
import os

# TODO: handle errors

class SolardClient(object):

    read_buffer = 4096

    def __init__(self, transport):
        self.transport = transport

    def run(self, *args, **kwargs):
        send = self.transport.send({'m': 'run', 'args': args, 'kwargs': kwargs})
        resp = self.transport.resp()
        return resp

    def copy_directory(self, _from, _to, use_sudo=False):
        # dir should open context on remote, and sync all files as one req/resp
        to_cp_files = []
        for root, dirs, files in os.walk(_from):
            for name in files:
                _from = os.path.join(root, name)
                _to = os.path.join(root.replace(_from, _to), name)
                to_cp_files.append((_from, _to))
        for _from, _to in to_cp_files:
            self._copy_file(_from, _to, use_sudo, empty_ok_resp=True)
        resp = self.transport.resp()
        return resp

    def _copy_file(self, _from, _to, use_sudo=False, empty_ok_resp=False):
        # TODO: separate empty_ok_resp from copy args
        transport = self.transport
        f_size = os.stat(_from).st_size
        data = {'m': 'copy_file',
                'args': (_to, use_sudo, f_size),
                's': True}
        if empty_ok_resp:
            data['empty_ok_resp'] = True
        send = transport.send(data)
        transport.send_stream_start(add_size=False)
        to_read = f_size
        with open(_from, 'rb') as f:
            while to_read > 0:
                data = f.read(self.read_buffer)  # expose sendfile there
                transport.send_stream_data(data)
                to_read -= len(data)
        assert to_read == 0
        return True

    def copy_file(self, _from, _to, use_sudo=False):
        self._copy_file(_from, _to, use_sudo)
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
    c = SolardClient(transport=SolardTCPClient('localhost', 5555))
    print c.run('hostname')
    print c.copy('/tmp/a', '/tmp/bbb/a.%s' % (time.time()))
    print c.copy('/tmp/bbb', '/tmp/s/ccc%s' % (time.time()))
