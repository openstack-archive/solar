from gevent import monkey
monkey.patch_all()


from gevent.server import StreamServer
import socket

import msgpack
import struct
import errno
import sys
import traceback


from types import GeneratorType
from solard.logger import logger
from solard.core import SolardContext, SolardIface


SERVER_BUFF = 4096
HDR = "<I"
HDR_SIZE = struct.calcsize(HDR)

INT_DEFAULT_REPLY_TYPE = 0
INT_GENERATOR_REPLY_TYPE = 1


class SolardTCPException(Exception):
    pass


class ReadFailure(SolardTCPException):
    pass


class SolardTCPHandler(object):

    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.ctx = SolardContext()
        self._wrote = False

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
            print '--------------------'
            print repr(d)
            print '--------------------'
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
        data = {'st': 2, 'res': res}
        self._write(**data)

    def _write_ok_gen(self, res):
        data = {'st': 20, 'res': res}
        self._write(**data)

    # def _write_ok_stream(self, res):
    #     data = {'st': 30, 'res': res}
    #     self._write(**data)

    # def _write_stream_data(self, data):
    #     self.sock.sendall(data)

    def _write_gen_end(self):
        data = {'st': 21, 'res': None}
        self._write(**data)

    def _write_failure(self, exception, reason, tb=""):
        data = {'st': 0, 'exception': exception, 'reason': reason, 'tb': tb}
        self._write(**data)

    def _write_err(self, error):
        logger.info("Client error: %s" % error)
        data = {'st': 1, 'error': error}
        self._write(**data)

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



class SolardTCPServer(StreamServer):

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        StreamServer.__init__(self, *args, **kwargs)

    def handle(self, sock, address):
        try:
            logger.debug("New from %s:%d" % address)
            h = SolardTCPHandler(sock, address)
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





if __name__ == '__main__':
    s = SolardTCPServer(('0.0.0.0', 5555))
    s.serve_forever()
