import os
from Jumpscale import j

JSConfigClient = j.baseclasses.object_config


class SonicServer(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.sonic.server.1
           name** = "default" (S)
           host = "127.0.0.1" (S)
           port = 1491 (I)
           password = "123456" (S)
           timeout = 300
           """

    def _init(self, **kwargs):
        self.config_path = j.sal.fs.joinPaths(j.dirs.CFGDIR, "sonic_config_%s.cfg" % self.name)
        if self.host == "localhost":
            self.host = "127.0.0.1"

        # NOT SURE NEXT IS CORRECT
        # if self.host == "127.0.0.1" and j.core.myenv.platform_is_osx:
        #     # ofcourse not ok, but is not for production anyhow, osx does not support the 127.0.0.1
        #     self.host = "0.0.0.0"

        self._default_client = None

    def start(self):
        """
        Starts sonic server in tmux
        """
        self._write_config()
        self.startupcmd.start()

    @property
    def _path(self):

        p = "%s/sonic_db/%s" % (j.core.myenv.config["DIR_VAR"], self.name)
        j.sal.fs.createDir("%s/kv" % p)
        j.sal.fs.createDir("%s/fst" % p)
        return p

    def _write_config(self):
        cfg_template = j.sal.fs.joinPaths(j.sal.fs.getDirName(os.path.abspath(__file__)), "sonic_config.cfg")
        args = {
            "host": self.host,
            "port": self.port,
            "password": self.password,
            "timeout": self.timeout,
            "datapath": self._path,
        }
        j.tools.jinja2.file_render(path=cfg_template, dest=self.config_path, **args)
        return self.config_path

    @property
    def default_client(self):
        if not self._default_client:
            self._default_client = j.clients.sonic.get(
                name="default", host=self.host, port=self.port, password=self.password
            )
            self._default_client.save()
        return self._default_client

    def stop(self):
        self._log_info("stop sonic server")
        self._write_config()
        self.startupcmd.stop()

    def destroy(self):
        self.stop()
        j.sal.fs.remove(self._path)

    @property
    def startupcmd(self):
        cmd = "sonic -c {}".format(self.config_path)
        return j.servers.startupcmd.get(name="sonic", cmd_start=cmd, ports=[self.port])
