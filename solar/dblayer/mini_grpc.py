import struct
from threading import local

from hyper import HTTP20Connection


class Grpc(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.threadlocal = local()

    @property
    def connection(self):
        if not hasattr(self.threadlocal, 'connection'):
            self.threadlocal.connection = HTTP20Connection(
                self.host, self.port
            )
        return self.threadlocal.connection

    def request(self, method, path, object_, RespClass, timeout):
        """Sends a request to a GRPC and returns a response object"""
        serialized = object_.SerializeToString()
        body = b'\0' + struct.pack('>L', len(serialized)) + serialized
        connection = self.connection
        sid = connection.putrequest(method, path)
        for header in [
            ('grpc-timeout', '{}S'.format(timeout)),
            ('grpc-encoding', 'identity'),
            ('grpc-accept-encoding', 'identity,deflate,gzip'),
            ('te', 'trailers'),
            ('content-type', 'application/grpc'),
            ('content-length', str(len(body))),
        ]:
            self.connection.putheader(*header, stream_id=sid)
        self.connection.endheaders(
            message_body=body,
            final=True,
            stream_id=sid
        )
        resp = self.connection.get_response(sid)
        resp_data = resp.read()[5:]
        resp_object = RespClass()
        resp_object.ParseFromString(resp_data)
        return resp_object
