from Jumpscale import j
import redis


class ZDBClientBase(j.baseclasses.object_config):
    def _init(self, jsxobject=None, **kwargs):
        if "admin" in kwargs:
            admin = kwargs["admin"]
        else:
            admin = self.admin

        if admin:
            self.nsname = "default"

        self.type = "ZDB"

        self.redis = _patch_redis_client(
            j.clients.redis.get(ipaddr=self.addr, port=self.port, fromcache=False, ping=False)
        )

        self.nsname = self.nsname.lower().strip()

        self._logger_enable()

        if admin:

            if self.secret_:
                # authentication should only happen in zdbadmin client
                self._log_debug("AUTH in namespace %s" % (self.nsname))
                self.redis.execute_command("AUTH", self.secret_)

        else:

            if self.nsname in ["default", "system"]:
                raise j.exceptions.Base("a non admin namespace cannot be default or system")

            # DO NOT AUTOMATICALLY CREATE THE NAMESPACE !!!!!
            # only go inside namespace if not in admin mode
            self._select_namespace()

        assert self.ping()

    def _select_namespace(self, nsname=None):
        if not nsname is None:
            self.nsname = nsname

        if self.secret_ is "":
            self._log_debug("select namespace:%s with NO secret" % (self.nsname))
            self.redis.execute_command("SELECT", self.nsname)
        else:
            self._log_debug("select namespace:%s with a secret" % (self.nsname))
            self.redis.execute_command("SELECT", self.nsname, self.secret_)

    def _key_encode(self, key):
        return key

    def _key_decode(self, key):
        return key

    def set(self, data, key=None):
        if key is None:
            key = ""
        return self.redis.execute_command("SET", key, data)

    def get(self, key):
        return self.redis.execute_command("GET", key)

    def exists(self, key):
        return self.redis.execute_command("EXISTS", key) == 1

    def delete(self, key):
        if not key:
            raise j.exceptions.Value("key must be provided")
        self.redis.execute_command("DEL", key)

    def flush(self):
        """
        will remove all data from the database DANGEROUS !!!!
        This is only allowed on private and password protected namespace
        You need to select the namespace before running the command.
        :return:
        """
        if not self.nsname in ["default", "system"]:
            self._select_namespace()
            self.redis.execute_command("FLUSH")

    def stop(self):
        pass

    @property
    def nsinfo(self):
        cmd = self.redis.execute_command("NSINFO", self.nsname)
        return _parse_nsinfo(cmd.decode())

    def list(self, key_start=None, reverse=False):
        """
        list all the keys in the namespace

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                        if False, walk from older to newer keys
                        if True walk from newer to older keys
                        defaults to False
        :param reverse: bool, optional
        :return: list of keys
        :rtype: [str]
        """
        result = []
        for key, data in self.iterate(key_start=key_start, reverse=reverse, keyonly=True):
            result.append(key)
        return result

    def iterate(self, key_start=None, reverse=False, keyonly=False):
        """
        walk over all the namespace and yield (key,data) for each entries in a namespace

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                if False, walk from older to newer keys
                if True walk from newer to older keys
                defaults to False
        :param reverse: bool, optional
        :param keyonly: [description], defaults to False
        :param keyonly: bool, optional
        :raises e: [description]
        """

        next = None
        data = None

        if key_start is not None:
            next = self.redis.execute_command("KEYCUR", self._key_encode(key_start))
            if not keyonly:
                data = self.get(key_start)
            yield (key_start, data)

        CMD = "SCANX" if not reverse else "RSCAN"

        while True:
            try:
                if not next:
                    response = self.redis.execute_command(CMD)
                else:
                    response = self.redis.execute_command(CMD, next)
                # format of the response
                # see https://github.com/threefoldtech/0-db/tree/development#scan
            except redis.ResponseError as e:
                if e.args[0] == "No more data":
                    return
                raise e

            (next, results) = response
            for item in results:
                keyb, size, epoch = item
                key_new = self._key_decode(keyb)
                data = None
                if not keyonly:
                    data = self.redis.execute_command("GET", keyb)
                yield (key_new, data)

    @property
    def count(self):
        """
        :return: return the number of entries in the namespace
        :rtype: int
        """
        return self.nsinfo["entries"]

    def ping(self):
        """
        go to default namespace & ping
        :return:
        """
        return self.redis.ping()


def _patch_redis_client(redis):
    # don't auto parse response for set, it's not 100% redis compatible
    # 0-db does return a key after in set
    for cmd in ["SET", "DEL"]:
        if cmd in redis.response_callbacks:
            del redis.response_callbacks[cmd]
    return redis


def _parse_nsinfo(raw):
    def empty(line):
        line = line.strip()
        if len(line) <= 0 or line[0] == "#" or ":" not in line:
            return False
        return True

    info = {}
    for line in filter(empty, raw.splitlines()):
        key, val = line.split(":")
        try:
            val = int(val)
            info[key] = val
            continue
        except ValueError:
            pass
        try:
            val = float(val)
            info[key] = val
            continue
        except ValueError:
            pass

        info[key] = str(val).strip()
    return info
