from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class RsyncClient(JSConfigClient):

    _SCHEMATEXT = """
        @url =  jumpscale.rsync.client
        name** = "default" (S)
        host = "127.0.0.1" (S)
        port = 873 (I)
        login = "" (S)
        password_ = "" (S)
        secret_ = "" (S)
        """

    def _init(self, **kwargs):
        self.options = "-r --delete-after --modify-window=60 --compress --stats  --progress"
        self._local = j.tools.executorLocal

    def _pad(self, dest):
        if len(dest) != 0 and dest[-1] != "/":
            dest += "/"
        return dest

    def syncFromServer(self, src, dest):
        src = self._pad(src)
        dest = self._pad(dest)
        if src == dest:
            return
        j.tools.path.get(dest).mkdir_p()
        cmd = "rsync -av %s %s %s" % (src, dest, self.options)
        self._log_debug(cmd)
        self._local.execute(cmd)

    def syncToServer(self, src, dest):
        src = self._pad(src)
        dest = self._pad(dest)
        if src == dest:
            return
        cmd = "rsync -av %s %s %s" % (src, dest, self.options)
        self._log_debug(cmd)
        self._local.execute(cmd)

    def sync(self, src, dest):
        """
        can only sync from server to client
        """
        src = self._pad(src)
        dest = self._pad(dest)
        if src == dest:
            return
        cmd = "rsync %s %s %s" % (src, dest, self.options)
        self._log_debug(cmd)
        self._local.execute(cmd)
