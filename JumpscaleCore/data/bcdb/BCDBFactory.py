from Jumpscale import j

from .BCDB import BCDB
from .BCDBModel import BCDBModel
from .BCDBModelBase import BCDBModelBase

import os
import sys
from .connectors.redis.RedisServer import RedisServer
import time

TESTTOOLS = j.baseclasses.testtools


class BCDBFactory(j.baseclasses.factory_testtools, TESTTOOLS):

    __jslocation__ = "j.data.bcdb"

    def _init(self, **kwargs):

        self._log_debug("bcdb starts")
        self._loaded = False
        self._path = j.sal.fs.getDirName(os.path.abspath(__file__))
        self._config_data_path = j.core.tools.text_replace("{DIR_CFG}/bcdb_config")

        self._code_generation_dir_ = None

        self._BCDBModelClass = BCDBModel  # j.data.bcdb._BCDBModelClasses
        self._BCDBModelBase = BCDBModelBase
        self._config = {}

        # load the system models
        system_meta_path = j.core.tools.text_replace(
            "{DIR_CODE}/github/threefoldtech/jumpscaleX_core/JumpscaleCore/data/bcdb/models_system/meta.toml"
        )
        j.data.schema.add_from_path(system_meta_path)

        self.__master = None

    def threebotserver_require(self, timeout=120):
        timeout2 = j.data.time.epoch + timeout
        while j.data.time.epoch < timeout2:
            res = j.sal.nettools.tcpPortConnectionTest("localhost", 6380)
            if res and j.core.db.get("threebot.starting") == None:
                self._master_set(False)
                return
        raise j.exceptions.Base("please start threebotserver, could not reach in '%s' seconds." % timeout)

    @property
    def _master(self):
        if self.__master is None:
            # see if a threebot starting
            if not j.core.db:
                # no choice but to say we are master
                return True
            if j.core.db.get("threebot.starting"):
                print(" ** WAITING FOR THREEBOT TO STARTUP, STILL LOADING")
                res = j.sal.nettools.waitConnectionTest("localhost", 6380, timeout=240)
                if res:
                    time.sleep(10)  # lets wait 10 more sec
                    # the server did answer, lets now wait till the threebot.starting is gone
                    timeout = j.data.time.epoch + 60
                    while j.data.time.epoch < timeout:
                        if j.core.db.get("threebot.starting") is None:
                            self.__master = False
                            return (
                                self.__master
                            )  # means we found a threebot who was started properly, can now start as slave
                raise j.exceptions.Base("threebotserver is starting but did not succeed within 5 min")

            if j.sal.nettools.tcpPortConnectionTest("localhost", 6380):
                # print("** AM WORKING AS SLAVE, BCDB WILL BE READONLY **")
                self.__master = False
            else:
                self.__master = True
        return self.__master

    # def _treebot_set(self, val=True): #ALREADY DONE IN THREEBOTSERVER
    #     self._master_set(val)
    #     if val:
    #         j.core.db.set("threebot.starting", ex=120, value="1")
    #     else:
    #         j.core.db.delete("threebot.starting")

    def recover_schemas(self, force=True, simulate=False):
        path = j.core.tools.text_replace("{DIR_CFG}/bcdb")
        for i in j.sal.fs.listFilesInDir(path, filter="*.toml"):
            data = j.data.serializers.toml.load(i)
            totalnr = len(data.values())
            nr = 0
            processed = []
            first = True
            for item in data.values():
                nr += 1
                newest = totalnr == nr  # this means its the last one
                for d in item:
                    md5 = d["md5"]
                    processed.append(md5)
                    text = d["text"]
                    url = d["url"]
                    if "@url" not in text:
                        print(" - ERROR: url not in text !!!, will overrule")
                    # don't save
                    s = j.data.schema.get_from_text(text, save=False, url=url)
                    # need to remember the last one in the list
                    if first:
                        print(f"{s.url}")
                        first = False
                    if not j.data.schema.meta.schema_exists(md5=md5):
                        if s._md5 != md5:
                            print(
                                f" - md5 mismatch, means old schema type prob (before refactor) {s._md5}:{md5} [{newest}]"
                            )
                        else:
                            print(f" - missing schema {md5} [{newest}]")
                    else:
                        s2 = j.data.schema.get(md5=md5)
                        if s._md5 != s2._md5:
                            print(f" - md5 mismatch, means old schema type prob, was in DB {s._md5}:{md5} [{newest}]")
                        else:
                            print(f" - exists & same {md5} [{newest}]")

                    assert s.url == d["url"]
                    if not simulate:
                        s = j.data.schema.get_from_text(text, newest=newest, url=url)  # will save in right way
                        # we need to remember the old md5's
                        s._md5 = md5
                        j.data.schema.meta.schema_set(s, newest=False)

    def _master_set(self, val=True):
        self.__master = val

    @property
    def _readonly(self):
        return not self._master

    def config_reload(self):
        self._loaded = False
        self._load()

    def _load(self):

        if not self._loaded:

            self._log_debug("LOAD CONFIG BCDB")

            # will make sure the toml schema's are loaded
            j.data.schema.add_from_path("%s/models_system" % self._dirpath)

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
        if "system" not in self._children:
            storclient = j.clients.sqlitedb.client_get(bcdbname="system", readonly=self._readonly)
            self._children["system"] = self._get(name="system", storclient=storclient)
        return self._children["system"]

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

        assert j.sal.process.checkProcessRunning("zdb") is False
        assert j.sal.process.checkProcessRunning("sonic") is False

    def start_servers_threebot_zdb_sonic(self, test=False, reset=False):
        """
        kosmos 'j.data.bcdb.start_servers_threebot_zdb_sonic()'

        starts all required services for the BCDB to work for threebot
        :return: (sonic, zdb) server instance
        """
        self.system
        # because will be visible on filesystem
        adminsecret_ = j.core.myenv.adminsecret

        if reset:
            zdb = j.servers.zdb.get(name="threebot")
            zdb.destroy()
            s = j.servers.sonic.get(name="threebot")
            s.destroy()

        if j.sal.nettools.tcpPortConnectionTest("localhost", 9900) is False:
            z = j.servers.zdb.get(name="threebot", adminsecret_=adminsecret_)
            z.start()

        if j.sal.nettools.tcpPortConnectionTest("localhost", 1491) is False:
            s = j.servers.sonic.get(name="threebot", port=1491, adminsecret_=adminsecret_)
            s.start()

        s = j.servers.sonic.get(name="threebot")
        assert s.adminsecret_ == adminsecret_
        z = j.servers.zdb.get(name="threebot")
        assert z.adminsecret_ == adminsecret_

        # TODO: would be best to login into the ZDB through admin interface and check that the passwd is ok

        self._core_zdb = z

        return (s, z)

    def start_servers_test_zdb_sonic(self, reset=False):

        admin_secret = "123456"
        namespaces_secret = "1234"
        namespaces = ["test"]

        cl = j.servers.zdb.test_instance_start(
            namespaces=namespaces, admin_secret=admin_secret, namespaces_secret=namespaces_secret, restart=reset
        )
        # the test_instance will test the zdb instance (ping & data dir exists)
        # name of the zdb server is test_instance

        if j.core.myenv.platform_is_linux:
            if reset:
                sonic_server = j.servers.sonic.default
                sonic_server.stop()
            if j.sal.nettools.tcpPortConnectionTest("localhost", 1492) is False:
                s = j.servers.sonic.get(name="testserver", port=1492, adminsecret_=admin_secret)
                s.start()
            s = j.servers.sonic.get(name="testserver")
            s.start()
            assert s.adminsecret_ == admin_secret
        else:
            s = None

        z = j.servers.zdb.get(name="testserver")
        assert z.adminsecret_ == admin_secret

        self._core_zdb = z

        return (s, z)

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
            if name in self._children:
                continue
            if name == "system":
                continue
            storclient = self._get_storclient(name)
            if storclient:
                bcdb = self._get(name, storclient)
                self._children[name] = bcdb
        return self._children

    def index_rebuild(self, name=None, storclient=None, recover_schemas=True):
        """
        kosmos 'j.data.bcdb.index_rebuild(name="system")'
        kosmos 'j.data.bcdb.index_rebuild(recover_schemas=False)'
        kosmos 'j.data.bcdb.index_rebuild()'

        can get a stor client by e.g.
            storclient = j.clients.sqlitedb.client_get(bcdbname="system")
            storclient = j.clients.zdb.client_get...

        if you use a stor client then the metadata for BCDB will not be used


        :return:
        """
        if recover_schemas:
            j.data.bcdb.recover_schemas()
        if not name:
            for bcdb in self.instances.values():
                bcdb.index_rebuild()
        elif storclient:
            bcdb = self._get(name, storclient=storclient)
            bcdb.index_rebuild()
        elif name == "system":
            bcdb = self.system
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

    def reset_connections(self):
        """
        will remove all remembered connections
        :return:
        """
        # self._load()
        j.sal.fs.remove(self._config_data_path)
        self._config = {}
        self._children = j.baseclasses.dict()
        self._loaded = False

    def stop(self, name=None):
        if not name:
            v = list(self.instances.values())
            for bcdb in v:
                bcdb.stop()
        elif name == "system":
            pass
        else:
            bcdb = self.get(name=name)
            bcdb.stop()

    def export(self, name=None, bcdbname=None, path=None, yaml=True, data=True, encrypt=False):
        """Export all models and objects

        kosmos 'j.data.bcdb.export(name="system")'
        kosmos 'j.data.bcdb.export()'

        :param path: path to export to
        :type path: str

        :param name: is the name of the backup, if not chosen will be like '06_Mar_2020_05_00_00'

        """
        if not name:
            name = j.data.time.getLocalTimeHRForFilesystem()

        if not path:
            path = j.core.tools.text_replace("{DIR_VAR}/bcdb_exports/%s" % name)

        if not name and j.sal.fs.exists(path):
            j.sal.fs.remove(path)

        if not bcdbname:
            for bcdb in list(self.instances.values()):
                self.export(name=name, bcdbname=bcdb.name, path=path, yaml=yaml, data=data, encrypt=encrypt)
            return
        elif bcdbname == "system":
            bcdb = self.system
            path2 = "%s/system" % (path)
        else:
            path2 = "%s/%s" % (path, bcdbname)
            bcdb = self.get(name=bcdbname)

        bcdb._export(path=path2, yaml=yaml, data=data, encrypt=encrypt)

        schema_path = j.core.tools.text_replace("{DIR_CFG}/schema_meta.msgpack")
        # Validate that the schema has saved before exporting
        j.data.schema.meta.save()
        j.sal.fs.copyFile(schema_path, "%s/schema_meta.msgpack" % path)

    def import_(self, path=None, data=True, encryption=False, interactive=False, reset=True):
        """
        import back

        kosmos 'j.data.bcdb.import_()'

        if path not specified will look at path you are in, if schema_meta.msgpack found will use that path

        remark:
        if you need to copy data from remote example ssh rsync
        rm -rf /sandbox/var/bcdb_exports
        rsync -rav -e ssh --delete root@explorer.testnet.grid.tf:/sandbox/var/bcdb_exports_03_05/ /sandbox/var/bcdb_exports/


        :param name:
        :param path:
        :return:
        """

        if j.sal.nettools.tcpPortConnectionTest("localhost", 6380):
            raise j.exceptions.Base("Cannot import threebot is running")

        j.data.bcdb._master_set()

        if not path:
            if j.sal.fs.exists(f"{j.sal.fs.getcwd()}/schema_meta.msgpack"):
                path = f"{j.sal.fs.getcwd()}"
            else:
                path = j.core.tools.text_replace("{DIR_VAR}/bcdb_exports/")

        if reset:
            # we can remove all
            if interactive:
                if not j.core.tools.ask_yes_no(
                    "Importing will reset your all your BCDB. Are you sure you want to continue?"
                ):
                    return
            self.destroy_all()

        self.start_servers_threebot_zdb_sonic()

        self._log_info(f"will import BCDB's from path: {path}")

        ## import all schemas
        j.data.schema.meta.load(path=f"{path}/schema_meta.msgpack")
        j.data.schema.meta.save()

        # make sure we have our schema's back in /sandbox/cfg/bcdb
        for schema in j.data.schema.schemas_all.values():
            j.data.schema.meta.schema_backup(schema)

        paths = j.sal.fs.listDirsInDir(path, recursive=False, dirNameOnly=False)
        for path in paths:
            self._import_bcdb(path=path, data=data, encryption=encryption)

        self.verify()

    def verify(self, names=[]):
        """
        kosmos 'j.data.bcdb.verify()'
        """

        self.start_servers_threebot_zdb_sonic()

        if j.sal.nettools.tcpPortConnectionTest("localhost", 6380):
            raise j.exceptions.Base("Cannot import threebot is running")

        j.data.bcdb._master_set()
        j.tools.executor.local

        for bcdb in j.data.bcdb.instances.values():
            if names:
                if bcdb.name not in names:
                    continue

            bcdb.verify()

        self._log_info(f"VERIFY COMPLETED AND OK FOR ALL BCDB.")

    def _import_bcdb(self, path=None, data=True, encryption=False):

        assert j.sal.fs.exists(path)

        if j.sal.fs.getBaseName(path) == "system":
            self.system._import_(path=path, interactive=False, data=data, encryption=encryption)
        else:
            path_bcdbconfig = f"{path}/bcdbconfig.yaml"
            assert j.sal.fs.exists(path_bcdbconfig)
            config = j.data.serializers.yaml.load(path_bcdbconfig)

            if not "name" in config:
                raise j.exceptions.Input(f"name needs to be in {path_bcdbconfig}, is the name of the bcdb")

            name = config["name"]

            if config["type"] not in ["zdb", "sqlite", "redis"]:
                # these types usually myjobs instance
                self._log_warning(f"only zdb, sqlite redis are supported your type is: {config['type']}")
                return
            bcdb = self.get_for_threebot(name, namespace=config.get("namespace"), ttype=config["type"])
            # lets check package config of the bcdb is the same

            bcdb._import_(path=path, interactive=False, data=data, encryption=encryption)

    def destroy_all(self):
        """
        destroy all remembered BCDB's
        SUPER DANGEROUS
        all data will be lost
        :return:
        """
        if not self._master:
            raise j.exceptions.Base("cannot destroy BCDB when not master")

        self._load()
        names = [name for name in self._config.keys()]
        try:
            self.threebot_stop()  # stop the threebot ones
        except:
            pass
        j.servers.tmux.kill()  # kill all tmux sessions

        self._children = j.baseclasses.dict()
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

        j.sal.fs.remove(j.core.tools.text_replace("{DIR_CFG}/schema_meta.msgpack"))
        j.sal.fs.remove(j.core.tools.text_replace("{DIR_CFG}/bcdb"))

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

            if name in self._children:
                self._children.pop(name)

            self._config.pop(name)
            self._config_write()

        self._loaded = False

    def get_for_threebot(self, name, namespace=None, ttype=None):
        """
        used by actors in threebot
        :param namespace:
        :param ttype:
        :param instance:
        :return:
        """
        self._log_debug(f"get bcdb: name:{name} namespace:{namespace} type:{ttype}")

        if j.data.bcdb.exists(name=name):
            bcdb = self.get(name=name)
            return bcdb

        if ttype not in ["zdb", "sqlite", "redis"]:
            raise j.exceptions.Input("ttype can only be zdb or sqlite")
        assert name
        if ttype == "zdb":
            zdb = self._core_zdb  # has been started in start_servers_threebot_zdb_sonic
            assert namespace
            adminsecret_ = j.core.myenv.adminsecret
            self._log_debug("get zdb admin client")
            zdb_admin = zdb.client_admin_get()
            if not zdb_admin.namespace_exists(namespace):
                zdb_admin.namespace_new(namespace, secret=adminsecret_, maxsize=0, die=True)
            storclient = zdb.client_get(name=name, secret=adminsecret_, nsname=namespace)
        elif ttype == "sqlite":
            assert not namespace  # should be empty only relevant in ZDB
            storclient = j.clients.sdb.client_get(bcdbname=name)
        elif ttype == "redis":
            assert not namespace  # should be empty only relevant in ZDB
            storclient = j.clients.rdb.client_get(bcdbname=name)
        else:
            raise j.exceptions.Input("only redis, sqlite and zdb supported")

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
            if name in self._children:
                # print("name:'%s' in instances on bcdb" % name)
                return self._children[name]
        if not self.exists(name=name):
            self._new(name=name, storclient=storclient)  # we create object in config of bcdb factory
        if name in self._config and not storclient:
            storclient = self._get_storclient(name)
        b = self._get(name=name, storclient=storclient, reset=reset)  # make instance of bcdb

        assert name in self._children

        return b

    def _get_vfs(self):
        from .BCDBVFS import BCDBVFS

        return BCDBVFS(self.instances)

    def _get_storclient(self, name):
        if name == "system":
            return j.clients.sqlitedb.client_get(bcdbname="system")
        data = self._config[name]

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
            else:
                raise j.exceptions.Input("cannot find zdb on port:%s" % data["port"])
        elif data["type"] == "rdb":
            if "addr" not in data:
                data["addr"] = "localhost"
            if "port" not in data:
                data["port"] = 6379
            if "secret" not in data:
                data["secret"] = ""
            storclient = j.clients.rdb.client_get(
                bcdbname=name, addr=data["addr"], port=data["port"], secret=data["secret"]
            )
        elif data["type"] == "sdb":
            storclient = j.clients.sqlitedb.client_get(bcdbname=name)
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
        self._children[name] = BCDB(storclient=storclient, name=name, reset=reset, readonly=self._readonly)
        return self._children[name]

    def _config_write(self):
        data = j.data.serializers.msgpack.dumps(self._config)
        data_encrypted = j.data.nacl.default.encryptSymmetric(data)
        j.sal.fs.writeFile(self._config_data_path, data_encrypted)

    def _new(self, name, storclient=None, reset=False):
        """
        create a new nce
        :param name:
        :param storclient: optional
            e.g. j.clients.rdb.client_get()  (would be the core redis
            e.g. j.clients.zdb.client_get() would be a zdb client
            e.g. j.clients.sqlitedb.client_get() would be a sqlite client

            if not specified then will be storclient = j.clients.sqlitedb.client_get(nsname="system")

        :return:
        """

        self._log_info("new bcdb:%s" % name)

        if self.exists(name=name):
            if not reset:
                raise j.exceptions.Input("cannot create new bcdb '%s' already exists, and reset not used" % name)

        if not storclient:
            storclient = j.clients.sqlitedb.client_get(bcdbname=name)

        data = {}
        assert isinstance(storclient.type, str)

        if storclient.type == "SDB":
            data["type"] = "sdb"
            # link to which redis to connect to (name of the redis client in JSX)
        elif storclient.type == "RDB":
            data["addr"] = storclient.addr
            data["port"] = storclient.port
            data["secret"] = storclient.secret
            data["type"] = "rdb"
            # link to which redis to connect to (name of the redis client in JSX)
        elif storclient.type == "ZDB":
            data["namespace"] = storclient.nsname
            data["addr"] = storclient.addr
            data["port"] = storclient.port
            data["secret"] = storclient.secret_
            data["type"] = "zdb"
        else:
            raise RuntimeError()

        self._config[name] = data
        self._config_write()
        self._load()

        if not self._master:
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

        raise RuntimeError("not implemented")
        # bcdb_instance.meta._migrate_meta(schema)

    def redis_server_get(self, port=6380, secret=None, addr="127.0.0.1"):
        self.redis_server = RedisServer(bcdb=self, port=port, secret=secret, addr=addr)
        self.redis_server._init2(bcdb=self, port=port, secret=secret, addr=addr)
        return self.redis_server

    def _test_redisserver_get(self, type="sqlite"):

        redis = j.servers.startupcmd.get("bcdb_redis_test")
        redis.stop()
        redis.wait_stopped()

        bcdb = self._test_bcdb_get(type)

        cmd = (
            """
                . {DIR_BASE}/env.sh;
                kosmos 'j.data.bcdb.get("%s").redis_server_start(port=6381)'
                """
            % bcdb.name
        )

        schema = """
                @url = despiegk.test2
                llist2 = "" (LS)
                name** = ""
                email** = ""
                nr** =  0
                date_start** =  0 (D)
                description = ""
                cost_estimate = 0.0 #this is a comment
                llist = []
                llist3 = "1,2,3" (LF)
                llist4 = "1,2,3" (L)
                """
        db, model = self._test_model_get(type=type, schema=schema, datagen=False)
        self._redisserver_startupcmd = j.servers.startupcmd.get(
            name="bcdb_redis_test", cmd_start=cmd, ports=[6381], executor="tmux"
        )
        self._redisserver_startupcmd.start()
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6381, timeout=15)
        return db, model

    def _test_bcdb_get(self, type="sqlite", reset=False):
        """
        ONLY USE THIS BCDB GET FOR THE TESTS
        """
        if not j.clients.zdb.exists("testserver"):
            reset = True
        if reset or not j.sal.nettools.tcpPortConnectionTest("localhost", 9901):
            # get the test servers in tmux
            self.start_servers_test_zdb_sonic(reset=reset)
        if type == "rdb":
            j.core.db
            storclient = j.clients.rdb.client_get(bcdbname="test_rdb")
            bcdb = self.get(name="test_rdb", storclient=storclient, reset=True)
        elif type == "sqlite":
            storclient = j.clients.sqlitedb.client_get(bcdbname="test_sqlite")
            bcdb = self.get(name="test_sqlite", storclient=storclient, reset=True)
        elif type == "zdb":
            storclient = j.clients.zdb.testserver
            storclient.flush()
            assert storclient.nsinfo["public"] == "no"
            assert storclient.ping()
            bcdb = self.get(name="test_zdb", storclient=storclient, reset=True)
        else:
            raise j.exceptions.Base("only rdb,zdb,sqlite for stor")

        assert bcdb.storclient == storclient

        bcdb.reset()  # empty

        assert bcdb.storclient.count == 1

        return bcdb

    def _test_model_get(self, type="zdb", schema=None, datagen=False):
        """

        kosmos 'j.data.bcdb._test_model_get(type="zdb",datagen=True)'
        kosmos 'j.data.bcdb._test_model_get(type="sqlite",datagen=True)'
        kosmos 'j.data.bcdb._test_model_get(type="rdb",datagen=True)'

        :param reset:
        :param type:
        :param schema:
        :return:
        """

        if not schema:
            schema = """
            @url = despiegk.test
            0:  llist2 = "" (LS)
            1:  name** = ""
            2:  email** = ""
            3:  nr** = 0
            4:  date_start** = 0 (D)
            5:  description = ""
            6:  token_price** = "10 USD" (N)
            7:  hw_cost = 0.0 #this is a comment
            8:  llist = []
            9:  llist3 = "1,2,3" (LF)
            10: llist4 = "1,2,3" (L)
            11: llist5 = "1,2,3" (LI)
            12: U = 0.0
            13: pool_type = "managed,unmanaged" (E)
            """

        type = type.lower()

        bcdb = self._test_bcdb_get(type=type)
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

    def test_core(self):
        """
        will test the core tests which should run everywhere
        the tests with sonic will not run on osx

        kosmos 'j.data.bcdb.test_core()'

        """
        # "redisbase"
        tests = ["base", "meta_test", "async", "models", "acls", "sqlitestor", "unique_data", "subschemas", "sqlite"]
        errors = 0
        for name in tests:
            errors += self._tests_run(name=name, die=False)

        if errors > 0:
            raise j.exceptions.Base("error in test for bcdb:%s" % errors)

    def test(self, name=""):
        """
        following will run all tests

        kosmos 'j.data.bcdb.test()'

        """

        self._tests_run(name=name, die=True)
        return "OK"
