from Jumpscale import j


class RedisConfig(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = jumpscale.redis_config.client
    name** = "" (S)
    addr = "127.0.0.1" (ipaddr)
    port = 6379 (ipport)
    password_ = "" (S)
    ardb_patch = false (B)
    unixsocket = "" (S)
    set_patch = false (B)
    ssl = false (B)
    # sslkey = false (B)
    # ssl_keypath = "" (S)
    """

    def _init(self, **kwargs):
        self._redis = None

    def _init3(self, **kwargs):
        if "ssl" in kwargs:
            assert kwargs["ssl"] is False
        assert self.ssl == False

        # TODO: need to deal with SSL (NOT URGENT BECAUSE WILL BE USING WIREGUARD EVERYWHERE ON GRID)
        # also redis natively does not support SSL

        # if ssl_keyfile and ssl_certfile:
        #     # check if its a path, if yes load
        #     kwargs["ssl"] = True
        #     # means path will be used for sslkey at redis client
        #     kwargs["sslkey"] = True
        #
        # r = JSConfigBase.get(
        #     self, name=name, id=id, die=die, create_new=create_new, childclass_name=childclass_name, **kwargs
        # )
        #
        # if ssl_keyfile and ssl_certfile:
        #     # check if its a path, if yes safe the key paths into config
        #     r.ssl_keys_save(ssl_keyfile, ssl_certfile)

    # @property
    # def ssl_certfile_path(self):
    #     """
    #     :return: ssl_certificate file path
    #     :rtype: str
    #     """
    #
    #     p = j.sal.fs.getDirName(self.ssl_keypath) + "cert.pem"
    #     if self.sslkey:
    #         return p
    #
    # @property
    # def ssl_keyfile_path(self):
    #     """
    #     :return: ssl_key file path
    #     :rtype: str
    #     """
    #
    #     p = j.sal.fs.getDirName(self.ssl_keypath) + "key.pem"
    #     if self.sslkey:
    #         return p

    @property
    def redis(self):
        if self._redis is None:

            if self.unixsocket:
                unixsocket = self.unixsocket
            else:
                unixsocket = None

            if self.addr:
                addr = self.addr
                port = self.port
            else:
                addr = None
                port = None

            if self.password_:
                password = self.password_
            else:
                password = None

            if self.ssl:
                raise j.exceptions.Base("not supported")
                self._redis = j.clients.redis.get(
                    ipaddr=addr,
                    port=port,
                    password=password,
                    unixsocket=unixsocket,
                    ardb_patch=self.ardb_patch,
                    set_patch=self.set_patch,
                    ssl=self.ssl,
                    ssl_keyfile=self.ssl_keyfile_path,
                    ssl_certfile=self.ssl_certfile_path,
                    ssl_cert_reqs=None,
                    ssl_ca_certs=None,
                )
            else:

                self._redis = j.clients.redis.get(
                    ipaddr=addr,
                    port=port,
                    password=password,
                    unixsocket=unixsocket,
                    ardb_patch=self.ardb_patch,
                    set_patch=self.set_patch,
                    # ssl=self.ssl,
                    # ssl_cert_reqs=None,
                    # ssl_ca_certs=None,
                )

        return self._redis

    # def ssl_keys_save(self, ssl_keyfile, ssl_certfile):
    #     """
    #     :param ssl_keyfile: ssl_key file path
    #     :type ssl_keyfile: str
    #     :param ssl_certfile: ssl_certificate
    #     :type ssl_certfile: str
    #     """
    #
    #     if j.sal.fs.exists(ssl_keyfile):
    #         ssl_keyfile = j.sal.fs.readFile(ssl_keyfile)
    #     if j.sal.fs.exists(ssl_certfile):
    #         ssl_certfile = j.sal.fs.readFile(ssl_certfile)
    #     j.sal.fs.writeFile(self.ssl_certfile_path, ssl_certfile)
    #     j.sal.fs.writeFile(self.ssl_keyfile_path, ssl_keyfile)

    def __str__(self):
        return "redis:%-14s %-25s:%-4s (ssl:%s)" % (self.name, self.addr, self.port, self.ssl)

    __repr__ = __str__
