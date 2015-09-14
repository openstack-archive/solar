#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License attached#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import msgpack

import socket
import errno
import struct


HDR = '<I'
HDR_SIZE = struct.calcsize(HDR)

CLIENT_BUFF = 4096


class ClientException(Exception):
    pass


class ReadError(ClientException):
    pass


class RemoteException(ClientException):
    pass


class SolardTCPClient(object):

    def __init__(self, host, port, **kwargs):
        self.host = host
        self.port = port
        # self._connect_timeout = kwargs.get("connect_timeout", None)
        self._socket_timeout = kwargs.get("socket_timeout", None)
        self.sock = None
        self.auth = None
        self._streaming = False

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(self._socket_timeout)
            sock.connect((self.host, self.port))
        except Exception:
            sock.close()
            raise
        else:
            self.sock = sock
            if not self.initialize_with_auth():
                self.sock = None
                raise ClientException("Auth failed")
            return sock

    def initialize_with_auth(self):
        self.send(self.auth)
        resp = self.resp(close=False)
        return resp

    def disconnect(self):
        sock = self.sock
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            err_ = getattr(e, 'errno', None)
            if err_ not in (errno.ENOTCONN, errno.EBADF):
                raise
        ret = sock.close()
        self.sock = None
        return ret

    def send(self, data):
        assert self._streaming is False
        if self.sock is None:
            self.connect()
        _data = msgpack.packb(data)
        size = len(_data)
        hdr = struct.pack(HDR, size)
        return self.sock.sendall(hdr + _data)

    def send_stream_start(self, add_size=False):
        assert self._streaming is False
        self._streaming = True
        if add_size is not False:
            hdr = struct.pack(HDR, add_size)
            self.sock.sendall(hdr)
        return self.sock

    def send_stream_cont(self, add_size=False):
        assert self._streaming is True
        if add_size is not False:
            hdr = struct.pack(HDR, add_size)
            self.sock.sendall(hdr)
        return self.sock

    def send_stream_end(self):
        assert self._streaming is True
        self._streaming = False
        return self.sock

    def send_stream_data(self, data):
        assert self._streaming is True
        self.sock.sendall(data)  # TODO: expose sendfile easier
        # self._streaming = False

    def read(self):
        sock = self.sock
        d = sock.recv(HDR_SIZE)
        if not len(d) == HDR_SIZE:
            raise ReadError()
        size = struct.unpack(HDR, d)[0]
        d = []
        while True:
            b = min(size, CLIENT_BUFF)
            curr = sock.recv(b)
            d.append(curr)
            size -= len(curr)
            if not size:
                break
        return msgpack.unpackb(''.join(d))

    def _resp_result_gen(self, data):
        st = data['st']
        if st == 20:  # OK
            return data['res']
        elif st == 21:
            raise StopIteration()
        else:
            raise RemoteException(data)

    def _resp_result_stream(self, data):
        return data

    def _resp_result(self, data):
        st = data['st']
        if st == 2:  # OK
            return data['res']
        else:
            raise RemoteException(data)

    def _resp_gen(self, res, close):
        try:
            while True:
                yield res
                try:
                    res = self._resp_result_gen(self.read())
                except StopIteration:
                    break
                except Exception:
                    raise RemoteException(res)
        finally:
            if close:
                self.disconnect()

    def resp(self, close=True):
        recv = self.read()
        st = recv['st']
        if 20 <= st < 30:
            return self._resp_gen(recv, close)
        try:
            res = self._resp_result(recv)
        finally:
            if close:
                self.disconnect()
        return res
