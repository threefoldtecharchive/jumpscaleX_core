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
import socket

from .boxstream import get_stream_pair
from .crypto import SHSClientCrypto, SHSServerCrypto


class SHSClientException(Exception):
    pass


class SHSDuplexStream(object):
    def __init__(self):
        self.write_stream = None
        self.read_stream = None
        self.is_connected = False

    def write(self, data):
        self.write_stream.write(data)

    def read(self):
        return self.read_stream.read()

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

    def _handshake(self, reader, writer):
        data = reader.readexactly(64)
        if not self.crypto.verify_challenge(data):
            raise SHSClientException("Client challenge is not valid")

        writer.write(self.crypto.generate_challenge())

        data = reader.readexactly(112)
        if not self.crypto.verify_client_auth(data):
            raise SHSClientException("Client auth is not valid")

        writer.write(self.crypto.generate_accept())

    def handle_connection(self, socket, addr):
        rw = ReadWriter(socket)

        self.crypto.clean()
        self._handshake(rw, rw)
        keys = self.crypto.get_box_keys()
        self.crypto.clean()

        conn = SHSServerConnection.from_byte_streams(rw, rw, **keys)
        self.connections.append(conn)

        if self._on_connect:
            self._on_connect(conn)

    def server(self):
        server = StreamServer((self.host, self.port), self.handle_connection)  # creates a new server
        return server

    def listen(self):
        server = StreamServer((self.host, self.port), self.handle_connection)  # creates a new server
        server.serve_forever()

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

    def recv(self, size):
        return self.read_stream.read()

    def sendall(self, data):
        self.write_stream.write(data)


class SHSClient(SHSDuplexStream, SHSEndpoint):
    def __init__(self, host, port, client_kp, server_pub_key, ephemeral_key=None, application_key=None):
        SHSDuplexStream.__init__(self)
        SHSEndpoint.__init__(self)
        self.host = host
        self.port = port
        self.crypto = SHSClientCrypto(
            client_kp, server_pub_key, ephemeral_key=ephemeral_key, application_key=application_key
        )

    def _handshake(self, reader, writer):
        writer.write(self.crypto.generate_challenge())

        data = reader.readexactly(64)
        if not self.crypto.verify_server_challenge(data):
            raise SHSClientException("Server challenge is not valid")

        writer.write(self.crypto.generate_client_auth())

        data = reader.readexactly(80)
        if not self.crypto.verify_server_accept(data):
            raise SHSClientException("Server accept is not valid")

    def open(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        rw = ReadWriter(s)
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


class ReadWriter:
    def __init__(self, socket):
        self._socket = socket

    def recv(self, size):
        return self._socket.recv()

    def sendall(self, data):
        return self._socket.sendall(data)

    def closed(self):
        return self._socket.closed

    def readexactly(self, size):
        return self._socket.recv(size)

    def write(self, data):
        return self._socket.sendall(data)
