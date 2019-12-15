# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j

from .BCDB import BCDB
from .BCDBModel import BCDBModel

import os
import sys
from .connectors.redis.RedisServer import RedisServer


class BCDBFactory(j.baseclasses.factory_testtools):

    __jslocation__ = "j.data.bcdb"

    def _init(self, **kwargs):

        self._log_debug("bcdb starts")
        self._loaded = False
        self._path = j.sal.fs.getDirName(os.path.abspath(__file__))

        self._code_generation_dir_ = None

        j.clients.redis.core_get()  # just to make sure the redis got started

        self._instances = j.baseclasses.dict(name="BCDBS")
        self.children = self._instances

        self._BCDBModelClass = BCDBModel  # j.data.bcdb._BCDBModelClass

        # will make sure the toml schema's are loaded
        j.data.schema.add_from_path("%s/models_system" % self._dirpath)

        self.__master = None

    @property
    def _master(self):
        if self.__master == None:
            if j.sal.nettools.tcpPortConnectionTest("localhost", 6380):
                self.__master = False
            else:
                self.__master = True
        return self.__master

    def config_reload(self):
        self._loaded = False
        self._load()

    def unlock(self):
        base_path = j.core.tools.text_replace("{DIR_BASE}/var/bcdb/")
        instances = []
        instances = [j.sal.fs.getBaseName(instance_path) for instance_path in j.sal.fs.listDirsInDir(base_path)]
        for instance in instances:
            lock_path = j.sal.fs.joinPaths(base_path, instance, "lock")
            if j.sal.fs.exists(lock_path):
                j.sal.fs.remove(lock_path)
                self._log_info(f"BCDB instance {instance} unlocked")

    def lock(self):
        base_path = j.core.tools.text_replace("{DIR_BASE}/var/bcdb/")
        instances = []
        instances = [j.sal.fs.getBaseName(instance_path) for instance_path in j.sal.fs.listDirsInDir(base_path)]
        for instance in instances:
            lock_path = j.sal.fs.joinPaths(base_path, instance, "lock")
            if not j.sal.fs.exists(lock_path):
                j.sal.fs.touch(lock_path)
                self._log_info(f"BCDB instance {instance} unlocked")
        self.__master = True

    def _load(self):

        if not self._loaded:

            print("LOAD CONFIG BCDB")

            self._config_data_path = j.core.tools.text_replace("{DIR_CFG}/bcdb_config")
            if j.sal.fs.exists(self._config_data_path):
                data_encrypted = j.sal.fs.readFile(self._config_data_path, binary=True)
                try:
                    data = j.data.nacl.default.decryptSymmetric(data_encrypted)
                except Exception as e:
                    if str(e).find("Ciphertext failed") != -1:
                        raise j.exceptions.Base("%s cannot be decrypted with secret" % self._config_data_path)
                    raise e
                self._config = j.data.serializers.msgpack.loads(data)
            else:
                self._config = {}

            self._loaded = True

    @property
    def system(self):
        if "system" not in self._instances:
            storclient = j.clients.sqlitedb.client_get(namespace="system")
            self._instances["system"] = self._get(name="system", storclient=storclient)
        return self._instances["system"]

    def threebot_stop(self):
        """
        kosmos 'j.data.bcdb.threebot_stop()'
        stops the threebot sonic & zdb
        :return:
        """

        if j.sal.nettools.tcpPortConnectionTest("localhost", 9900):
            zdb = j.servers.zdb.get(name="threebot")
            zdb.stop()
        if j.sal.nettools.tcpPortConnectionTest("localhost", 1491):
            s = j.servers.sonic.get(name="threebot")
            s.stop()

        assert j.sal.process.checkProcessRunning("zdb") == False
        assert j.sal.process.checkProcessRunning("sonic") == False

    def threebot_zdb_sonic_start(self, reset=False):
        """
        kosmos 'j.data.bcdb.threebot_zdb_sonic_start()'

        starts all required services for the BCDB to work for threebot
        :return: (sonic, zdb) server instance
        """
        self.system
        # because will be visible on filesystem
        adminsecret_ = j.data.hash.md5_string(j.servers.threebot.default.adminsecret_)

        if reset:
            zdb = j.servers.zdb.get(name="threebot")
            zdb.destroy()
            s = j.servers.sonic.get(name="threebot")
            s.destroy()

        if j.sal.nettools.tcpPortConnectionTest("localhost", 9900) == False:
            z = j.servers.zdb.get(name="threebot", adminsecret_=adminsecret_)
            z.start()

        if j.sal.nettools.tcpPortConnectionTest("localhost", 1491) == False:
            s = j.servers.sonic.get(name="threebot", port=1491, adminsecret_=adminsecret_)
            s.start()

        s = j.servers.sonic.get(name="threebot")
        assert s.adminsecret_ == adminsecret_
        z = j.servers.zdb.get(name="threebot")
        assert z.adminsecret_ == adminsecret_

        # TODO: would be best to login into the ZDB through admin interface and check that the passwd is ok

        return (s, z)

    def get_test(self, reset=False):
        bcdb = j.data.bcdb.new(name="testbcdb")
        bcdb2 = j.data.bcdb._instances["testbcdb"]
        assert bcdb2.storclient == None
        return bcdb

    @property
    def _BCDBModelClass(self):
        return BCDBModel

    @property
    def WebDavProvider(self):
        from .connectors.webdav.BCDBResourceProvider import BCDBResourceProvider

        return BCDBResourceProvider()

    @property
    def instances(self):
        self._load()
        keys = [i for i in self._config.keys()]
        for name in keys:
            # don't reload the bcdb instance because its already
            if name in self._instances:
                continue
            if name == "system":
                continue
            storclient = self._get_storclient(name)
            if storclient:
                bcdb = self._get(name, storclient)
                self._instances[name] = bcdb

        return self._instances

    def index_rebuild(self, name=None, storclient=None):
        """
        kosmos 'j.data.bcdb.index_rebuild(name="system")'

        can get a stor client by e.g.
            storclient = j.clients.sqlitedb.client_get(namespace="system")
            storclient = j.clients.zdb.client_get...

        if you use a stor client then the metadata for BCDB will not be used


        :return:
        """
        if not name:
            for bcdb in self.instances:
                bcdb.index_rebuild()
        elif storclient:
            bcdb = self._get(name, storclient=storclient)
            bcdb.index_rebuild()
        elif name == "system":
            bcdb = self.get_system()
            bcdb.index_rebuild()
        else:
            bcdb = self.get(name=name)
            bcdb.index_rebuild()

    def check(self):
        """
        not implemented yet, will check the indexes & data
        :return:
        """
        self._load()
        # TODO:
        pass

    def reset(self):
        """
        will remove all remembered connections
        :return:
        """
        # self._load()
        j.sal.fs.remove(self._config_data_path)
        self._config = {}
        self._instances = j.baseclasses.dict()
        self._loaded = False

    def destroy_all(self):
        """
        destroy all remembered BCDB's
        SUPER DANGEROUS
        all data will be lost
        :return:
        """
        if not self._master:
            raise j.exceptions.Base("cannot destory BCDB when not master")

        self._load()
        names = [name for name in self._config.keys()]

        self.threebot_stop()  # stop the threebot ones
        j.servers.tmux.kill()  # kill all tmux sessions

        self._instances = j.baseclasses.dict()
        storclients = []
        for name in names:
            try:
                cl = self._get_storclient(name)
            except:
                continue
            if cl not in storclients:
                storclients.append(cl)
        for cl in storclients:
            if cl and cl.type == "ZDB" and cl.addr not in ["127.0.0.1", "localhost"]:
                raise j.exceptions.NotImplemented("TODO: need to delete remote namespace")
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_VAR}/bcdb"))
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_VAR}/zdb"))
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_VAR}/sonic_db"))
        j.sal.fs.remove(self._config_data_path)
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_VAR}/codegen"))
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_VAR}/capnp"))

        # leftovers in redis
        for key in j.core.db.keys("bcdb:*"):
            j.core.db.delete(key)
        for key in j.core.db.keys("rdb*"):
            j.core.db.delete(key)
        for key in j.core.db.keys("queue*"):
            j.core.db.delete(key)

        self._loaded = False
        self._load()
        assert self._config == {}

    def exists(self, name):
        """
        does the bcdb instance exist in the configuration
        :param name:
        :return:
        """
        self._load()
        if name == "system":
            return True
        return name in self._config

    def destroy(self, name):
        if not self._master:
            raise j.exceptions.Base("cannot destory BCDB when not master")
        self._load()
        assert name
        assert isinstance(name, str)

        if self.exists(name):

            bcdb = self.get(name=name)
            bcdb.reset()

            if name in self._instances:
                self._instances.pop(name)

            self._config.pop(name)
            self._config_write()

        self._loaded = False

    def get_for_threebot(self, namespace, ttype, instance):
        """
        used by actors in threebot
        :param namespace:
        :param ttype:
        :param instance:
        :return:
        """
        if ttype not in ["zdb", "sqlite", "redis"]:
            raise j.exceptions.Input("ttype can only be zdb or sqlite")

        name = "threebot_%s_%s" % (ttype, namespace)

        if j.data.bcdb.exists(name=name):
            return self.get(name=name)
        else:
            if ttype == "zdb":
                adminsecret_ = j.data.hash.md5_string(j.threebot.servers.core.adminsecret_)
                self._log_debug("get zdb admin client")
                zdb_admin = j.threebot.servers.core.zdb.client_admin_get()
                if not zdb_admin.namespace_exists(namespace):
                    zdb_admin.namespace_new(namespace, secret=adminsecret_, maxsize=0, die=True)
                storclient = j.threebot.servers.core.zdb.client_get(namespace, adminsecret_)
            elif ttype == "sqlite":
                storclient = j.clients.sqlitedb.client_get(namespace=namespace)
            elif ttype == "redis":
                storclient = j.clients.rdb.client_get(namespace=namespace)
            else:
                raise j.exceptions.Input("only redis, slqite and zdb supported")

            return self.get(name=name, storclient=storclient)

    def get(self, name, storclient=None, reset=False):
        """
        will create a new one or an existing one if it exists
        :param name:
        :param reset: will remove the data
        :param storclient: optional
            e.g. j.clients.rdb.client_get()  (would be the core redis
            e.g. j.clients.zdb.client_get() would be a zdb client
        :return:
        """
        self._load()
        assert isinstance(name, str)

        if not reset:
            if name in self._instances:
                # print("name:'%s' in instances on bcdb" % name)
                return self._instances[name]

        if name in self._config and not storclient:
            storclient = self._get_storclient(name)

        if not self.exists(name=name):
            self._new(name=name, storclient=storclient)  # we create object in config of bcdb factory

        b = self._get(name=name, storclient=storclient, reset=reset)  # make instance of bcdb

        assert name in self._instances

        return b

    def _get_vfs(self):
        from .BCDBVFS import BCDBVFS

        return BCDBVFS(self.instances)

    def _get_storclient(self, name):

        if name == "system":
            return j.clients.sqlitedb.client_get(namespace="system")

        data = self._config[name]
        storclient = None
        if data["type"] == "zdb":
            if j.sal.nettools.tcpPortConnectionTest(ipaddr=data["addr"], port=data["port"]):
                storclient = j.clients.zdb.client_get(
                    name=name,
                    namespace=data["namespace"],
                    addr=data["addr"],
                    port=data["port"],
                    secret=data["secret"],
                    mode="seq",
                )
        elif data["type"] == "rdb":
            storclient = j.clients.rdb.client_get(namespace=data["namespace"], redisconfig_name="core")
        elif data["type"] == "sdb":
            storclient = j.clients.sqlitedb.client_get(namespace=data["namespace"])
        else:
            raise j.exceptions.Input("type storclient not found:%s" % data["type"])
        return storclient

    def _get(self, name, storclient=None, reset=False):
        """[summary]
        get instance of bcdb
        :param name:
        :param storclient: can add this if bcdb instance doesn't exist
        :return:
        """
        # DO NOT CHANGE if_not_exist_die NEED TO BE TRUE
        self._instances[name] = BCDB(storclient=storclient, name=name, reset=reset)
        return self._instances[name]

    def _config_write(self):
        data = j.data.serializers.msgpack.dumps(self._config)
        data_encrypted = j.data.nacl.default.encryptSymmetric(data)
        j.sal.fs.writeFile(self._config_data_path, data_encrypted)

    def _new(self, name, storclient=None):
        """
        create a new instance
        :param name:
        :param storclient: optional
            e.g. j.clients.rdb.client_get()  (would be the core redis
            e.g. j.clients.zdb.client_get() would be a zdb client
            e.g. j.clients.sqlitedb.client_get() would be a sqlite client

            if not specified then will be storclient = j.clients.sqlitedb.client_get(nsname="system")

        :return:
        """

        self._log_info("new bcdb:%s" % name)

        # if name in self._instances:
        #     print("name:'%s' in instances on bcdb (new)" % name)
        #     return self._instances[name]
        #
        # if self.exists(name=name):
        #     if not reset:
        #         raise j.exceptions.Input("cannot create new bcdb '%s' already exists, and reset not used" % name)

        if not storclient:
            storclient = j.clients.sqlitedb.client_get(namespace=name)

        data = {}
        assert isinstance(storclient.type, str)

        if storclient.type == "SDB":
            data["namespace"] = storclient.nsname
            data["type"] = "sdb"
            # link to which redis to connect to (name of the redis client in JSX)
        elif storclient.type == "RDB":
            data["namespace"] = storclient.nsname
            data["type"] = "rdb"
            data["redisconfig_name"] = storclient._redis.redisconfig_name
            # link to which redis to connect to (name of the redis client in JSX)
        else:
            data["namespace"] = storclient.nsname
            data["addr"] = storclient.addr
            data["port"] = storclient.port
            data["secret"] = storclient.secret_
            data["type"] = "zdb"

        self._config[name] = data
        self._config_write()
        self._load()

        if self._master():
            # we have changed the config of bcdb, need to make sure server knows about it
            j.clients.bcdbmodel.server_config_reload()

    @property
    def _code_generation_dir(self):
        if not self._code_generation_dir_:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "models")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self._log_debug("codegendir:%s" % path)
            self._code_generation_dir_ = path
        return self._code_generation_dir_

    def migrate(self, base_url, second_url, bcdb="system", **kwargs):
        """
        """
        bcdb_instance = self.get(bcdb)
        base_model = bcdb_instance.model_get(url=base_url)
        second_model = bcdb_instance.model_get(url=second_url)
        # create new meta with new migration

        for model_s in second_model.find():
            overwrite = False
            for model_b in base_model.find():
                if model_b.name == model_s.name:
                    overwrite = True
                    if kwargs.items():
                        for key, val in kwargs.items():
                            second = getattr(model_s, "{}".format(val))
                            setattr(model_b, key, second)

                    model_b.save()
                    model_s.delete()
                    # overwtite
            if not overwrite:
                m = base_model.new()
                for prop in base_model.schema.properties:

                    if hasattr(model_s, "{}".format(prop.name)):
                        setattr(m, prop.name, getattr(model_s, "{}".format(prop.name)))
                m.save()
                model_s.delete()
                # create new one
        schema = bcdb_instance.schema_get(url=second_url)

        bcdb_instance.meta._migrate_meta(schema)

    def redis_server_get(self, port=6380, secret="123456", addr="127.0.0.1"):
        self.redis_server = RedisServer(bcdb=self, port=port, secret=secret, addr=addr)
        self.redis_server._init2(bcdb=self, port=port, secret=secret, addr=addr)
        return self.redis_server

    def _load_test_model(self, type="zdb", schema=None, datagen=False):
        """

        kosmos 'j.data.bcdb._load_test_model(type="zdb",datagen=True)'
        kosmos 'j.data.bcdb._load_test_model(type="sqlite",datagen=True)'
        kosmos 'j.data.bcdb._load_test_model(type="rdb",datagen=True)'

        :param reset:
        :param type:
        :param schema:
        :return:
        """

        if not schema:
            schema = """
            @url = despiegk.test
            llist2 = "" (LS)
            name*** = ""
            email** = ""
            nr** = 0
            date_start** = 0 (D)
            description = ""
            token_price** = "10 USD" (N)
            hw_cost = 0.0 #this is a comment
            llist = []
            llist3 = "1,2,3" (LF)
            llist4 = "1,2,3" (L)
            llist5 = "1,2,3" (LI)
            U = 0.0
            pool_type = "managed,unmanaged" (E)
            """

        type = type.lower()

        def startZDB():
            zdb = j.servers.zdb.test_instance_start()
            storclient_admin = zdb.client_admin_get()
            assert storclient_admin.ping()
            secret = "1234"
            storclient = storclient_admin.namespace_new(name="test_zdb", secret=secret)
            return storclient

        if not j.sal.nettools.tcpPortConnectionTest("localhost", 1491):
            j.servers.sonic.get(name="default").start()

        if type == "rdb":
            j.core.db
            storclient = j.clients.rdb.client_get(namespace="test_rdb")  # will be to core redis
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        elif type == "sqlite":
            storclient = j.clients.sqlitedb.client_get(namespace="test_sdb")
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        elif type == "zdb":
            storclient = startZDB()
            storclient.flush()
            assert storclient.nsinfo["public"] == "no"
            assert storclient.ping()
            bcdb = self.get(name="test", storclient=storclient, reset=True)
        else:
            raise j.exceptions.Base("only rdb,zdb,sqlite for stor")

        assert bcdb.storclient == storclient

        assert bcdb.name == "test"

        bcdb.reset()  # empty

        assert bcdb.storclient.get(0)
        assert bcdb.storclient.count == 1

        assert bcdb.name == "test"

        model = bcdb.model_get(schema=schema)

        # lets check the sql index is empty
        assert model.index.sql_index_count() == 0

        if type.lower() in ["zdb"]:
            # print(model.storclient.nsinfo["entries"])
            assert model.storclient.nsinfo["entries"] == 1

        assert len(model.find()) == 0

        if datagen:
            for i in range(3):
                model_obj = model.new()
                model_obj.llist.append(1)
                model_obj.llist2.append("yes")
                model_obj.llist2.append("no")
                model_obj.llist3.append(1.2)
                model_obj.date_start = j.data.time.epoch
                model_obj.U = 1.1
                model_obj.nr = i
                model_obj.token_price = "10 EUR"
                model_obj.description = "something"
                model_obj.name = "name%s" % i
                model_obj.email = "info%s@something.com" % i
                model_obj2 = model.set(model_obj)
            assert len(model.find()) == 3

        return bcdb, model

    def __str__(self):

        out = "## {GRAY}BCDBS: {BLUE}\n\n"

        for bcdb_name in self.instances.keys():
            out += " - %s\n" % bcdb_name

        out += "{RESET}"
        out = j.core.tools.text_replace(out)
        return out

    __repr__ = __str__

    def test(self, name=""):
        """
        following will run all tests

        kosmos 'j.data.bcdb.test()'
        kosmos 'j.data.bcdb.test("base")'


        """
        print(name)
        # CLEAN STATE
        j.servers.zdb.test_instance_stop()
        j.servers.sonic.default.stop()

        self._test_run(name=name)

        # CLEAN STATE
        j.servers.zdb.test_instance_stop()
        j.servers.sonic.default.stop()

        self._log_info("All TESTS DONE")
        return "OK"
