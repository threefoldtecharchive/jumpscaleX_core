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
from gevent.pool import Pool
from gevent import signal
import gevent
from gevent.server import StreamServer
from redis.exceptions import ConnectionError
from Jumpscale.servers.gedis.protocol import RedisResponseWriter, RedisCommandParser

JSBASE = j.baseclasses.object


class RedisServer(j.baseclasses.object):
    def _init2(self, bcdb=None, addr="127.0.0.1", port=6380, secret="123456"):
        self.bcdb = bcdb
        self._sig_handler = []
        #
        self.host = addr
        self.port = port  # 1 port higher than the std port
        self.secret = secret
        self.ssl = False
        # j.clients.redis.core_check()  #need to make sure we have a core redis

        self.init()

    def init(self, **kwargs):
        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))
        if self.ssl:
            self.ssl_priv_key_path, self.ssl_cert_path = self.sslkeys_generate()
            # Server always supports SSL
            # client can use to talk to it in SSL or not
            self.gevent_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handle_redis,
                keyfile=self.ssl_priv_key_path,
                certfile=self.ssl_cert_path,
            )
        else:
            self.gevent_server = StreamServer((self.host, self.port), spawn=Pool(), handle=self.handle_redis)
        # self.vfs = j.data.bcdb._get_vfs()

    def start(self):
        self._log_info("RUNNING")
        self.gevent_server.serve_forever()

    def stop(self):
        """
        stop receiving requests and close the server
        """
        # prevent the signal handler to be called again if
        # more signal are received
        for h in self._sig_handler:
            h.cancel()

        self._log_info("stopping server")
        self.gevent_server.stop()

    def handle_redis(self, socket, address):

        parser = RedisCommandParser(socket)
        response = RedisResponseWriter(socket)

        try:
            self._handle_redis(socket, address, parser, response)
        except ConnectionError as err:
            self._log_info("connection error: {}".format(str(err)))
        finally:
            parser.on_disconnect()
            self._log_info("close connection from {}".format(address))

    def _handle_redis(self, socket, address, parser, response):

        self._log_info("connection from {}".format(address))
        socket.namespace = "system"

        while True:
            request = parser.read_request()

            if request is None:
                self._log_debug("connection lost or tcp test")
                break

            if not request:  # empty list request
                self._log_debug("EMPTYLIST")
                continue

            cmd = request[0]
            redis_cmd = cmd.decode("utf-8").lower()

            if redis_cmd == "command":
                response.encode("OK")
                continue

            elif redis_cmd == "ping":
                response.encode("PONG")
                continue

            elif redis_cmd == "info":
                self.info_internal(response)
                continue

            elif redis_cmd == "select":
                if request[1] == b"0":
                    response.encode("OK")
                    continue
                response.error("DB index is out of range")
                continue

            elif redis_cmd in ["hscan"]:
                kwargs = parser.request_to_dict(request[3:])
                if not hasattr(self, redis_cmd):
                    response.error("COULD NOT FIND COMMAND:%s" % redis_cmd)
                    raise j.exceptions.Base("COULD NOT FIND COMMAND:%s" % redis_cmd)
                else:
                    method = getattr(self, redis_cmd)
                    start_obj = int(request[2].decode())
                    key = request[1].decode()
                    method(response, key, start_obj, **kwargs)
                continue

            else:
                redis_cmd = request[0].decode().lower()
                args = request[1:] if len(request) > 1 else []
                args = [x.decode() for x in args]

                if redis_cmd == "del":
                    redis_cmd = "delete"
                if not hasattr(self, redis_cmd):
                    response.error("COULD NOT FIND COMMAND:%s" % redis_cmd)
                    return

                method = getattr(self, redis_cmd)
                method(response, *args)
                continue

    def bcdb_model_init(self, response, bcdbname, url, md5, schema):

        if not j.data.bcdb.exists(bcdbname):
            response.error("COULD NOT FIND BCDB:%s" % bcdbname)
            return

        if bcdbname in [None, "", b""]:
            bcdbname = None

        if url in [None, "", b""]:
            url = None

        if md5 in [None, "", b""]:
            md5 = None

        if schema in [None, "", b""]:
            schema = None

        if not bcdbname:
            # means we can only reload
            j.data.bcdb.config_reload()
            response.encode("OK")
            return

        if md5:
            if md5 in j.data.schema.schemas:
                # means we know it schema not needed
                schema = None
            else:
                # means we don't know it yet, need to make sure schema based on url is removed out of cache
                if url and url in j.data.schema.schemas:
                    j.data.schema.schema_cache_remove(url)

        if schema:
            assert isinstance(schema, str)
            schema = j.data.schema.get_from_text(schema, url=url)
            url = schema.url

        assert url

        if not j.data.bcdb.exists(bcdbname):
            # need to make sure to load, because maybe a slave has added a new one
            j.data.bcdb.config_reload()

        bcdb = j.data.bcdb.get(bcdbname)

        if not j.data.schema.exists(url=url):
            response.error("COULD NOT FIND SCHEMA WITH URL:%s" % url)
            return

        model = bcdb.model_get(url=url)
        if md5:
            # double check schema is ok
            assert model.schema._md5 == md5
        model.index.sql_index_count()

        response.encode("OK")

    def info(self):
        return b"NO INFO YET"

    def auth(self, response, *args, **kwargs):
        # j.shell()
        response.encode("OK")

    def _split(self, key):
        """
        split function used in the "normal" methods
        (len, set, get, del)
        split the key into 3 composant:
        - category: objects or schema
        - url: url of the schema
        - key: actual key of the object
        :param key: full encoded key of an object. e.g: object:schema.url:key
        :type key: str
        :return: tuple of (category, url, key, model)
        :rtype: tuple
        """
        url = ""
        cat = ""
        if key.strip() == "":
            raise j.exceptions.Base("key cannot be empty")
        splitted = key.split(":")
        len_splitted = len(splitted)
        m = ""
        key = ""
        bcdb_name = splitted[0]
        if "schemas" in splitted[:2]:
            idx = splitted.index("schemas")
            cat = "schemas"
            url = splitted[idx + 1]
        else:
            if len_splitted == 3:
                cat = splitted[1]
                url = splitted[2]
            elif len_splitted == 4:
                cat = splitted[1]
                url = splitted[3]
            elif len_splitted == 5:
                cat = splitted[1]
                url = splitted[3]
                key = splitted[4]
        if url != "":
            # If we have a url we should be able to get the corresponding model if we already have seen that model
            # otherwise we leave the model to an empty string because it is tested further on to know that we have to set
            # this schema
            m = self.bcdb.get(bcdb_name).model_get(url=url)

        return (cat, url, key, m)

    def set(self, response, key, val, new=False):
        parse_key = key.replace(":", "/")
        if "schemas" in parse_key:
            try:
                self.vfs.add_schemas(val)
                response.encode("OK")
                return
            except:
                response.error("cannot set, key:'%s' not supported" % key)
        else:
            bcdb_name, url, id = self._parse_key(key)
            model = j.clients.bcdbmodel.get(name=bcdb_name, url=url)
            try:
                obj = model.new(data=val)
                obj.save()
                assert obj.id
                if new:
                    response.encode(obj.id)
                else:
                    response.encode("OK")
                return
            except:
                response.error("cannot set, key:'%s' not supported" % key)
        return

    def _parse_key(self, key):
        s = key.split(":")
        assert len(s) == 3
        bcdb_name, _, url_id = s
        url, id = url_id.split("/")
        id = int(id)
        bcdb_name = bcdb_name.lower().strip()
        return bcdb_name, url, id

    def get(self, response, key):
        if key == "schemas":
            res = {}
            for name, bcdb in self.bcdb.instances.items():
                res2 = []
                for model in bcdb.models:
                    res2.append(model.schema.text)
                res[name] = res2
            response.encode(j.data.serializers.json.dumps(res))
            return
        bcdb_name, url, id = self._parse_key(key)
        model = j.clients.bcdbmodel.get(name=bcdb_name, url=url)
        try:
            obj = model.get(id)
        except:
            response.error("cannot get, key:'%s' not found" % key)
        response.encode(obj._json)

    def delete(self, response, key):
        bcdb_name, url, id = self._parse_key(key)
        model = j.clients.bcdbmodel.get(name=bcdb_name, url=url)
        try:
            model.delete(id)
            response.encode(1)
            return
        except:
            response.error("cannot delete, key:'%s'" % key)

    def scan(self, response, startid, match="*", count=10000, *args):
        """

        :param scan: id to start from
        :param match: default *
        :param count: nr of items per page
        :return:
        """
        # in first version will only do 1 page, so ignore scan
        res = []
        for bcdb in self.bcdb.instances.values():
            name = bcdb.name
            if not bcdb.models:
                res.append("%s:schemas" % name)
                res.append("%s:data" % name)
            else:
                for model in bcdb.models:
                    res.append("{}:schemas:{}".format(name, model.schema.url))
                    res.append("{}:data:{}".format(name, model.schema.url))

        response._array(["0", res])

    def hset(self, response, key, id, val):
        key = f"{key}/{id}"
        return self.set(response, key, val)

    def hsetnew(self, response, key, id, val):
        key = f"{key}/{id}"
        return self.set(response, key, val, new=True)

    def hget(self, response, key, id):
        key = f"{key}/{id}"
        return self.get(response, key)

    def hdel(self, response, key, id):
        key = f"{key}/{id}"
        return self.delete(response, key)

    def hlen(self, response, key):
        bcdb_name, cat, model_url = key.split(":")
        model = self.bcdb.get(bcdb_name).model_get(url=model_url)
        response.encode(model.count())
        return

    def ttl(self, response, key):
        response.encode("-1")

    def type(self, response, type):
        """
        :param type: is the key we need to give type for
        :return:
        """
        try:
            response.encode("hash")
        except:
            response.encode("string")

    def _urls(self):
        urls = [i for i in self.bcdb.models]
        return urls

    def hscan(self, response, key, startid, count=10000):
        res = []
        cat, url, key, model = self._split(key)
        if cat == "schemas":
            res.append(model.key)
            res.append(model.schema.text)

        else:
            for obj in model.find():
                res.append(obj.id)
                res.append(obj._json)

        response._array(["0", res])
        return

    def info_internal(self, response, *args):
        C = """
        # Server
        redis_version:4.0.11
        redis_git_sha1:00000000
        redis_git_dirty:0
        redis_build_id:13f90e3a88f770eb
        redis_mode:standalone
        os:Darwin 17.7.0 x86_64
        arch_bits:64
        multiplexing_api:kqueue
        atomicvar_api:atomic-builtin
        gcc_version:4.2.1
        process_id:93263
        run_id:49afb34b519a889778562b7addb5723c8c45bec4
        tcp_port:6380
        uptime_in_seconds:3600
        uptime_in_days:1
        hz:10
        lru_clock:12104116
        executable:/Users/despiegk/redis-server
        config_file:

        # Clients
        connected_clients:1
        client_longest_output_list:0
        client_biggest_input_buf:0
        blocked_clients:52

        # Memory
        used_memory:11436720
        used_memory_human:10.91M
        used_memory_rss:10289152
        used_memory_rss_human:9.81M
        used_memory_peak:14691808
        used_memory_peak_human:14.01M
        used_memory_peak_perc:77.84%
        used_memory_overhead:2817866
        used_memory_startup:980704
        used_memory_dataset:8618854
        used_memory_dataset_perc:82.43%
        total_system_memory:17179869184
        total_system_memory_human:16.00G
        used_memory_lua:37888
        used_memory_lua_human:37.00K
        maxmemory:100000000
        maxmemory_human:95.37M
        maxmemory_policy:noeviction
        mem_fragmentation_ratio:0.90
        mem_allocator:libc
        active_defrag_running:0
        lazyfree_pending_objects:0

        # Persistence
        loading:0
        rdb_changes_since_last_save:66381
        rdb_bgsave_in_progress:0
        rdb_last_save_time:1538289882
        rdb_last_bgsave_status:ok
        rdb_last_bgsave_time_sec:-1
        rdb_current_bgsave_time_sec:-1
        rdb_last_cow_size:0
        aof_enabled:0
        aof_rewrite_in_progress:0
        aof_rewrite_scheduled:0
        aof_last_rewrite_time_sec:-1
        aof_current_rewrite_time_sec:-1
        aof_last_bgrewrite_status:ok
        aof_last_write_status:ok
        aof_last_cow_size:0

        # Stats
        total_connections_received:627
        total_commands_processed:249830
        instantaneous_ops_per_sec:0
        total_net_input_bytes:22576788
        total_net_output_bytes:19329324
        instantaneous_input_kbps:0.01
        instantaneous_output_kbps:6.20
        rejected_connections:2
        sync_full:0
        sync_partial_ok:0
        sync_partial_err:0
        expired_keys:5
        expired_stale_perc:0.00
        expired_time_cap_reached_count:0
        evicted_keys:0
        keyspace_hits:76302
        keyspace_misses:3061
        pubsub_channels:0
        pubsub_patterns:0
        latest_fork_usec:0
        migrate_cached_sockets:0
        slave_expires_tracked_keys:0
        active_defrag_hits:0
        active_defrag_misses:0
        active_defrag_key_hits:0
        active_defrag_key_misses:0

        # Replication
        role:master
        connected_slaves:0
        master_replid:49bcd83fa843f4e6657440b7035a1c2314766ac4
        master_replid2:0000000000000000000000000000000000000000
        master_repl_offset:0
        second_repl_offset:-1
        repl_backlog_active:0
        repl_backlog_size:1048576
        repl_backlog_first_byte_offset:0
        repl_backlog_histlen:0

        # CPU
        used_cpu_sys:101.39
        used_cpu_user:64.27
        used_cpu_sys_children:0.00
        used_cpu_user_children:0.00

        # Cluster
        cluster_enabled:0

        # Keyspace
        # db0:keys=10000,expires=1,avg_ttl=7801480
        """
        C = j.core.text.strip(C)
        response.encode(C)

    def __str__(self):
        out = "redisserver:bcdb"
        return out

    __repr__ = __str__
