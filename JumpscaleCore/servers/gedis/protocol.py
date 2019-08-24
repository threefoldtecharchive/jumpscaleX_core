from io import BytesIO

from Jumpscale import j
from redis.connection import Encoder, PythonParser, SocketBuffer
from redis.exceptions import ConnectionError


class RedisCommandParser(PythonParser):
    """
    Parse the command send from the client
    """

    def __init__(self, socket, socket_read_size=8192):
        super(RedisCommandParser, self).__init__(socket_read_size=socket_read_size)

        self._sock = socket

        # @TODO -- new redis exoects timeout param
        # remove this if condition when everyone updates to new redis package
        try:
            self._buffer = SocketBuffer(self._sock, self.socket_read_size)
        except TypeError:  # init needs extra parameter in new redis
            self._buffer = SocketBuffer(self._sock, self.socket_read_size, socket_timeout=60)

        self.encoder = Encoder(encoding="utf-8", encoding_errors="strict", decode_responses=False)

    def read_request(self):
        # rename the function to map more with server side
        return self.read_response()

    def request_to_dict(self, request):
        # request.pop(0) #first one is command it self
        key = None
        res = {}
        for item in request:
            item = item.decode()
            if key is None:
                key = item
                continue
            else:
                key = key.lower()
                res[key] = item
                key = None
        return res


class RedisResponseWriter(object):
    """Writes data back to client as dictated by the Redis Protocol."""

    def __init__(self, socket):
        self.socket = socket
        self.buffer = BytesIO()

    def encode(self, value):
        """Respond with data."""
        if value is None:
            self._write_buffer("$-1\r\n")
        elif isinstance(value, int):
            self._write_buffer(":%d\r\n" % value)
        elif isinstance(value, bool):
            self._write_buffer(":%d\r\n" % (1 if value else 0))
        elif isinstance(value, str):
            if "\n" in value:
                self._bulk(value)
            else:
                self._write_buffer("+%s\r\n" % value)
        elif isinstance(value, bytes):
            self._bulkbytes(value)
        elif isinstance(value, list):
            if value and value[0] == "*REDIS*":
                value = value[1:]
            self._array(value)
        elif hasattr(value, "__repr__"):
            self._bulk(value.__repr__())
        else:
            value = j.data.serializers.json.dumps(value, encoding="utf-8")
            self.encode(value)

        self._send()

    def status(self, msg="OK"):
        """Send a status."""
        self._write_buffer("+%s\r\n" % msg)
        self._send()

    def error(self, msg):
        """Send an error."""
        # print("###:%s" % msg)
        self._write_buffer("-ERR %s\r\n" % str(msg))
        self._send()

    def _bulk(self, value):
        """Send part of a multiline reply."""
        data = ["$", str(len(value)), "\r\n", value, "\r\n"]
        self._write_buffer("".join(data))

    def _array(self, value):
        """send an array."""
        self._write_buffer("*%d\r\n" % len(value))
        for item in value:
            self.encode(item)

    def _bulkbytes(self, value):
        data = [b"$", str(len(value)).encode(), b"\r\n", value, b"\r\n"]
        self._write_buffer(b"".join(data))

    def _write_buffer(self, data):
        if isinstance(data, str):
            data = data.encode()

        self.buffer.write(data)

    def _send(self):
        self.socket.sendall(self.buffer.getvalue())
        self.buffer = BytesIO()  # seems faster then truncating


class WebsocketResponseWriter:
    def __init__(self, socket):
        self.socket = socket

    def encode(self, data):
        self.socket.send(j.data.serializers.json.dumps(data, encoding="utf-8"))

    def error(self, msg):
        self.socket.send(msg)
