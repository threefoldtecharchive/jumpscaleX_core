import threading
import gevent


class StreamReaderBase:
    def __init__(self, stream, channel, queue, flag):
        self.stream = stream
        self.channel = channel
        self.queue = queue
        self.flag = flag
        self._stopped = False

    def run(self):
        """
        read until all buffers are empty and retrun code is ready
        """
        while not self.stream.closed and not self._stopped:
            buf = ""
            buf = self.stream.readline()
            if len(buf) > 0:
                self.queue.put((self.flag, buf))
            elif not self.channel.exit_status_ready():
                continue
            elif self.flag == "O" and self.channel.recv_ready():
                continue
            elif self.flag == "E" and self.channel.recv_stderr_ready():
                continue
            else:
                break
        self.queue.put(("T", self.flag))


class StreamReaderThreading(StreamReaderBase, threading.Thread):
    def __init__(self, stream, channel, queue, flag):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        StreamReaderBase.__init__(self, stream, channel, queue, flag)


class StreamReaderGevent(StreamReaderBase):
    def start(self):
        self.greenlet = gevent.spawn(self.run)

    def join(self):
        self.greenlet.join()
