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

# from gevent import monkey
# monkey.patch_all()


# from gevent.server import StreamServer

from SocketServer import ThreadingTCPServer, BaseRequestHandler
import socket

import threading
import errno
import msgpack
import time
import struct
import errno
import sys
import traceback
import pwd
import os

from types import GeneratorType

from solard.logger import logger
from solard.core import SolardContext, SolardIface
from solard.tcp_core import *


SERVER_BUFF = 4096


class SolardTCPException(Exception):
    pass


class ReadFailure(SolardTCPException):
    pass


class SolardTCPHandler(object):

    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.ctx = SolardContext()
        self.auth = None
        self._wrote = False
        self.forked = False

    def _read(self):
        # TODO: client closed connection
        try:
            size = struct.unpack(HDR, self.sock.recv(HDR_SIZE))[0]
        except:
            raise ReadFailure("Can't read header data")
        d = []
        while True:
            b = min(size, SERVER_BUFF)
            curr = self.sock.recv(b)
            if not curr:
                raise ReadFailure("No data")
            d.append(curr)
            size -= len(curr)
            assert size >= 0
            if not size:
                break
        self._wrote = False
        try:
            return msgpack.unpackb(''.join(d))
        except:
            raise

    def _read_stream(self, size=None):
        if size is None:
            try:
                size = struct.unpack(HDR, self.sock.recv(HDR_SIZE))[0]
            except:
                raise ReadFailure("Can't read header data")
        while True:
            b = min(size, SERVER_BUFF)
            curr = self.sock.recv(b)
            if not curr:
                if size > 0:
                    raise ReadFailure("Expected more data")
            size -= len(curr)
            assert size >= 0
            yield curr
            if not size:
                break

    def _write(self, **kwargs):
        assert self._wrote is False
        _data = msgpack.packb(kwargs)
        size = len(_data)
        hdr = struct.pack(HDR, size)
        self.sock.sendall(hdr + _data)
        self._wrote = True

    def _write_ok(self, res):
        # logger.debug("Ok sent")
        data = {'st': REPLY_OK, 'res': res}
        self._write(**data)

    def _write_ok_gen(self, res):
        data = {'st': REPLY_GEN_OK, 'res': res}
        self._write(**data)

    # def _write_ok_stream(self, res):
    #     data = {'st': 30, 'res': res}
    #     self._write(**data)

    # def _write_stream_data(self, data):
    #     self.sock.sendall(data)

    def _write_gen_end(self):
        data = {'st': REPLY_GEN_END, 'res': None}
        self._write(**data)

    def _write_failure(self, exception, reason, tb=""):
        data = {'st': REPLY_FAIL, 'exception': exception, 'reason': reason, 'tb': tb}
        self._write(**data)

    def _write_err(self, error):
        logger.info("Client error: %s" % error)
        data = {'st': REPLY_ERR, 'error': error}
        self._write(**data)

    def make_auth(self):
        # it's responsible for:
        # - checking auth
        # - forking if needed
        auth_data = self._read()
        if not auth_data:
            self._write_ok(False)
            return False
        req_user = auth_data.get('user')
        if not req_user:
            self._write_ok(False)
            return False
        proc_user = pwd.getpwuid(os.getuid())[0]
        logger.debug("Requested user %r", req_user)
        # TODO:
        # we may add there anything we want, checking in file etc
        # for now it's just `password`
        valid = auth_data.get('auth') == 'password'
        if not valid:
            self._write_ok(False)
            return False
        if req_user == proc_user:
            self._write_ok(True)
            return True
        # TODO: very naive
        if auth_data.get('sudo'):
            self._write_ok(True)
            return True
        # fork there
        child_pid = os.fork()
        if child_pid == 0:
            pw_uid = pwd.getpwnam(req_user).pw_uid
            pw_gid = pwd.getpwuid(pw_uid).pw_gid
            os.setgid(pw_gid)
            os.setuid(pw_uid)
            logger.debug("Child forked %d", os.getpid())
            self._fix_env(pw_uid)
            self.forked = True
            self._write_ok(True)
            return True
        return None

    def _fix_env(self, pw_uid):
        pw_dir = pwd.getpwuid(pw_uid).pw_dir
        os.environ['HOME'] = pw_dir


    def process(self):
        try:
            known_type = INT_DEFAULT_REPLY_TYPE
            input_data = self._read()
            if not input_data:
                return False
            method = input_data['m']
            meth = getattr(SolardIface, method)
            is_stream = input_data.get('s', False)
            logger.debug("Going to run %r", method)
            if is_stream:
                res = meth(self.ctx, self._read_stream, *input_data.get('args', ()), **input_data.get('kwargs', {}))
            else:
                res = meth(self.ctx, *input_data.get('args', ()), **input_data.get('kwargs', {}))
            if isinstance(res, GeneratorType):
                known_type = INT_GENERATOR_REPLY_TYPE
                try:
                    for curr in res:
                        self._wrote = False
                        self._write_ok_gen(curr)
                except:
                    raise
                finally:
                    try:
                        self._wrote = False
                        self._write_gen_end()
                    except Exception:  # ignore if eng gen couldn't be send
                        pass
                    self._wrote = True
            else:
                # if not input_data.get('empty_ok_resp', False):
                self._write_ok(res)
        except ReadFailure:
            return False
        except Exception as ex:
            if self._wrote:
                if known_type == INT_GENERATOR_REPLY_TYPE:
                    errno_ = getattr(ex, 'errno', None)
                    if errno_ in (errno.EPIPE, errno.ECONNRESET):
                        logger.debug(
                            "Client disconnected during generator based reply")
                    else:
                        logger.debug("Error during generator based reply")
                        raise
                else:
                    logger.error("Already wrote data, but got exception")
                    raise
            else:
                logger.exception("Got exception")
                self.handle_exception()
        return True

    def handle_exception(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.format_exception(exc_type, exc_value, exc_traceback)

        reason = str(exc_value)
        if not reason:
            reason = exc_type.__name__
        try:
            self._write_failure(exc_type.__name__, reason, tb)
        except:
            logger.warn("Failure when sending error response")
            raise
        finally:
            logger.exception("Got exception")


class SolardReqHandler(BaseRequestHandler):

    def handle(self):
        sock = self.request
        address = self.client_address
        h = SolardTCPHandler(sock, address)
        try:
            logger.debug("New from %s:%d" % address)
            auth_state = h.make_auth()
            if auth_state is False:
                logger.debug("Failed auth")
                return
            if auth_state is None:
                # child forked
                # we don't wait there, but in recycler
                return
            while True:
                if not h.process():
                    logger.debug("End from %s:%d" % address)
                    break
                else:
                    logger.debug("Waiting for more from %s:%d" % address)
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
        finally:
            sock.close()
            if h.forked:
                # if forked we can safely exit now
                os._exit(0)


class SolardTCPServer(ThreadingTCPServer):

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        # StreamServer.__init__(self, *args, **kwargs)
        ThreadingTCPServer.__init__(self, *args, **kwargs)

    def dummy_recycle_childs(self):
        # dummy child recycler, turns each 3 seconds
        def child_recycler():
            while True:
                try:
                    pid, status = os.waitpid(-1, 0)
                    logger.debug("Child %r ended with status=%d", pid, status)
                except OSError as e:
                    if e.errno != errno.ECHILD:
                        raise
                    time.sleep(3)
        th = threading.Thread(target=child_recycler)
        th.daemon = True
        th.start()

    @staticmethod
    def run_solard(port):
        s = SolardTCPServer(('0.0.0.0', port), SolardReqHandler)
        s.dummy_recycle_childs()
        return s.serve_forever()



if __name__ == '__main__':
    SolardTCPServer.run_solard(5555)
