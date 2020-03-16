from collections import namedtuple
from io import BytesIO


class CommandError(Exception):
    pass


class Disconnect(Exception):
    pass


Error = namedtuple("Error", ("message",))


class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            b"+": self.handle_simple_string,
            b"-": self.handle_error,
            b":": self.handle_integer,
            b"$": self.handle_string,
            b"*": self.handle_array,
            b"%": self.handle_dict,
        }

    def handle_request(self, stream):
        first_byte = stream.read(1)
        if not first_byte:
            raise Disconnect()

        try:
            # Delegate to the appropriate handler based on the first byte.
            return self.handlers[first_byte](stream)
        except KeyError:
            raise CommandError("bad request")

    def handle_simple_string(self, stream):
        return stream.readline().rstrip(b"\r\n")

    def handle_error(self, stream):
        return Error(stream.readline().rstrip(b"\r\n"))

    def handle_integer(self, stream):
        return int(stream.readline().rstrip(b"\r\n"))

    def handle_string(self, stream):
        # First read the length ($<length>\r\n).
        length = int(stream.readline().rstrip(b"\r\n"))
        if length == -1:
            return None  # Special-case for NULLs.
        length += 2  # Include the trailing \r\n in count.
        return stream.read(length)[:-2]

    def handle_array(self, stream):
        num_elements = int(stream.readline().rstrip(b"\r\n"))
        return [self.handle_request(stream) for _ in range(num_elements)]

    def handle_dict(self, stream):
        num_items = int(stream.readline().rstrip(b"\r\n"))
        elements = [self.handle_request(stream) for _ in range(num_items * 2)]
        return dict(zip(elements[::2], elements[1::2]))

    def write_response(self, stream, data):
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        stream.write(buf.getvalue())

    def _write(self, buf, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        if isinstance(data, bytes):
            buf.write(b"$%d\r\n%s\r\n" % (len(data), data))
        elif isinstance(data, int):
            buf.write(b":%d\r\n" % data)
        elif isinstance(data, Error):
            buf.write(b"-%s\r\n" % Error.message)
        elif isinstance(data, (list, tuple)):
            buf.write(b"*%d\r\n" % len(data))
            for item in data:
                self._write(buf, item)
        elif isinstance(data, dict):
            buf.write("%%%d\r\n" % len(data))
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])
        elif data is None:
            buf.write(b"$-1\r\n")
        else:
            raise CommandError("unrecognized type: %s" % type(data))

    def _write_buffer(self, buf, data):
        if isinstance(data, str):
            data = data.encode()
        buf.write(data)
