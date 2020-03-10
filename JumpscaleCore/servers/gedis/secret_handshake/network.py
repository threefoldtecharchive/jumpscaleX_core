# Copyright (c) 2017 PySecretHandshake contributors (see AUTHORS for more details)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from gevent.server import StreamServer

from gevent import socket


from .boxstream import get_stream_pair
from .crypto import SHSClientCrypto, SHSServerCrypto


class SHSClientException(Exception):
    pass


class SHSDuplexStream(object):
    def __init__(self):
        self.write_stream = None
        self.read_stream = None
        self.is_connected = False
        self._buf = b""

    def write(self, data):
        self.write_stream.write(data)

    def read(self, size=-1):
        if size == -1:
            if self._buf:
                data = self._buf
                self._buf = b""
                return data
            else:
                return self.read_stream.read()

        count = len(self._buf)
        while count < size:
            msg = self.read_stream.read()
            if not msg:
                return None
            count = count + len(msg)
            self._buf += msg

        data = self._buf[:size]
        self._buf = self._buf[size:]
        return data

    def readline(self):
        if self._buf:
            data = self._buf[:]
            self._buf = b""
        else:
            data = self.read()

        i = data.index(b"\r\n")
        while i == -1:
            data += self.read()
            i = data.index(b"\r\n")
        self._buf = data[i + 2 :]
        return data[: i + 2]

    def close(self):
        self.write_stream.close()
        self.read_stream.close()
        self.is_connected = False

    def __iter__(self):
        for msg in self.read_stream:
            yield msg


class SHSEndpoint(object):
    def __init__(self):
        self._on_connect = None
        self.crypto = None

    def on_connect(self, cb):
        self._on_connect = cb

    def disconnect(self):
        raise NotImplementedError


class SHSServer(SHSEndpoint):
    def __init__(self, host, port, server_kp, application_key=None):
        super(SHSServer, self).__init__()
        self.host = host
        self.port = port
        self.crypto = SHSServerCrypto(server_kp, application_key=application_key)
        self.connections = []
        self._server = StreamServer((self.host, self.port), self.handle_connection)  # creates a new server

    def _handshake(self, reader, writer):
        data = reader.read(64)
        if not self.crypto.verify_challenge(data):
            raise SHSClientException("Client challenge is not valid")

        writer.write(self.crypto.generate_challenge())
        writer.flush()

        data = reader.read(112)
        if not self.crypto.verify_client_auth(data):
            raise SHSClientException("Client auth is not valid")

        writer.write(self.crypto.generate_accept())
        writer.flush()

    def handle_connection(self, socket, addr):
        rw = socket.makefile("rwb")

        self.crypto.clean()
        self._handshake(rw, rw)
        keys = self.crypto.get_box_keys()
        self.crypto.clean()

        conn = SHSServerConnection.from_byte_streams(rw, rw, **keys)
        self.connections.append(conn)

        if self._on_connect:
            self._on_connect(conn, addr, self.crypto.remote_pub_key)

    def listen(self):
        self._server.serve_forever()

    def server(self):
        return self._server

    def disconnect(self):
        for connection in self.connections:
            connection.close()


class SHSServerConnection(SHSDuplexStream):
    def __init__(self, read_stream, write_stream):
        super(SHSServerConnection, self).__init__()
        self.read_stream = read_stream
        self.write_stream = write_stream

    @classmethod
    def from_byte_streams(cls, reader, writer, **keys):
        reader, writer = get_stream_pair(reader, writer, **keys)
        return cls(reader, writer)


class SHSClient(SHSDuplexStream, SHSEndpoint):
    def __init__(self, host, port, client_kp, server_pub_key, ephemeral_key=None, application_key=None):
        SHSDuplexStream.__init__(self)
        SHSEndpoint.__init__(self)
        self.host = host
        self.port = port
        self.crypto = SHSClientCrypto(
            client_kp, server_pub_key, ephemeral_key=ephemeral_key, application_key=application_key
        )
        self._sock = None

    def _handshake(self, reader, writer):
        writer.write(self.crypto.generate_challenge())
        writer.flush()

        data = reader.read(64)
        if not self.crypto.verify_server_challenge(data):
            raise SHSClientException("Server challenge is not valid")

        writer.write(self.crypto.generate_client_auth())
        writer.flush()

        data = reader.read(80)
        if not self.crypto.verify_server_accept(data):
            raise SHSClientException("Server accept is not valid")

    def open(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock = s
        s.connect((self.host, self.port))
        rw = s.makefile("rwb")
        self._handshake(rw, rw)

        keys = self.crypto.get_box_keys()
        self.crypto.clean()

        self.read_stream, self.write_stream = get_stream_pair(rw, rw, **keys)
        self.writer = rw
        self.is_connected = True
        if self._on_connect:
            self._on_connect()

    def disconnect(self):
        self.close()
        self._sock = None
