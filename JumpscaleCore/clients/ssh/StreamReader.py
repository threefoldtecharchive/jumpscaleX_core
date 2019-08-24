import threading


class StreamReader(threading.Thread):
    def __init__(self, stream, channel, queue, flag):
        super(StreamReader, self).__init__()
        self.stream = stream
        self.channel = channel
        self.queue = queue
        self.flag = flag
        self._stopped = False
        self.setDaemon(True)

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
