from Jumpscale import j

try:
    import ujson as json
except BaseException:
    import json

import msgpack
import time


class LoggerClient(j.baseclasses.object_config):
    """
    A logging client for logs pushed to redis (using our RedisLogger)
    Can be used to fetch logs from any machine
    """

    _SCHEMATEXT = """
        @url = jumpscale.clients.logger.1
        name** = ""
        redis_addr = "127.0.0.1" (ipaddr)
        redis_port = 6379 (ipport)
        redis_secret = ""
        """

    def _init(self, **kwargs):
        self._redis_client = None
        self._log_dir = j.core.tools.text_replace("{DIR_VAR}/logs/")
        j.sal.fs.createDir(self._log_dir)

    @property
    def db(self):
        if self._redis_client is None:
            self._redis_client = j.clients.redis.get(
                addr=self.redis_addr, port=self.redis_port, secret=self.redis_secret
            )

        return self._redis_client

    # def _data_container_set(self, container, appname):
    #     assert isinstance(container, list)
    #     assert len(container) == 1000
    #     j.shell()
    #     logdir = "%s/%s" % (self._log_dir, appname)
    #     if not j.sal.fs.exists(logdir):
    #         return []
    #     else:
    #         data = msgpack.dumps(container)
    #         j.shell()
    #         w

    def _data_container_get(self, identifier, appname):
        logdir = "%s/%s" % (self._log_dir, appname)
        if not j.sal.fs.exists(logdir):
            raise j.exceptions.Input("cannot find:%s" % logdir)

        logcontainer_path = "%s/%s/%s.msgpack" % (self._log_dir, appname, identifier * 1000)
        if not j.sal.fs.exists(logcontainer_path):
            raise j.exceptions.Input("cannot find:%s" % logcontainer_path)

        res = msgpack.loads(j.sal.fs.readFile(logcontainer_path, True))
        assert len(res) == 1000

        return res

    def _data_container_ids_get_from_time(self, epoch_from=None, epoch_to=None, appname=None):
        """
        find which data container exists from right timeframe
        return all container id's e.g. 1 = 1000 which correspond to the epoch_from/to
        :return:
        """
        if not epoch_from:
            epoch_from = 0
        if not epoch_to:
            epoch_to = j.data.time.epoch
        assert appname
        assert isinstance(epoch_from, int)
        assert isinstance(epoch_to, int)

        logdir = "%s/%s" % (self._log_dir, appname)
        if not j.sal.fs.exists(logdir):
            return []
        res = []
        for path in j.sal.fs.listFilesInDir(logdir):
            epoch_on_fs = int(j.sal.fs.statPath(path).st_ctime)
            if epoch_on_fs + 1 > epoch_from and epoch_on_fs - 1 < epoch_to:
                log_id_found_start = int(int(j.sal.fs.getBaseName(path).split(".", 1)[0]) / 1000)
                if log_id_found_start not in res:
                    res.append(log_id_found_start)
        res.sort()
        if len(res) > 0:
            if res[0] > 1:
                # we need to always look at the container before the first one if not 0, put at start
                res.insert(0, res[0] - 1)
        return res

    def delete(self, identifier):
        """delete an alert

        :param identifier: alert unique identifier
        :type identifier: str
        :return: 1 or 0 (if it was not already there)
        :rtype: int
        """
        return self.db.hdel(self.rediskey_logs, identifier)

    def delete_all(self, appname=None):
        """
        delete all alerts
        """
        if not appname:
            for key in self.db.keys("logs:*"):
                self.db.delete(key)
            logdir = self._log_dir
        else:
            for key in self.db.keys("logs:%s:*" % appname):
                self.db.delete(key)
            logdir = "%s/%s" % (self._log_dir, appname)
        j.core.tools.delete(logdir)

    def get(self, identifier, appname=None, die=True):
        """
        only workds for redis

        :param identifier:
        :param appname:
        :param die:
        :return:
        """
        s = j.core.myenv.loghandler_redis._redis_get(identifier=identifier, appname=appname, die=die)
        if not die and not s:
            return None
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        assert isinstance(s, str)
        return json.loads(s)

    def walk_reverse(self, method, time_from=None, time_to=None, maxitems=10000, appname=None, lastid=None, args={}):
        """
        will only walk over redis, so the last 1000 messages guaranteed (upto 2000)
        :param method:
        :param time_from:
        :param time_to:
        :param maxitems:
        :param appname:
        :param args:
        :return:
        """
        if time_from:
            epoch_from = j.data.types.datetime.clean(time_from)
        else:
            epoch_from = 0
        if time_to:
            epoch_to = j.data.types.datetime.clean(time_to)
        else:
            epoch_to = j.data.time.epoch + 1

        if not appname:
            appname = j.application.appname

        def walk(appname, lastid):
            nrdone = 1
            incrkey = "logs:%s:incr" % (appname)
            lastkey = int(self.db.get(incrkey))
            firstkey = lastkey - 2000
            res = []
            for i in range(lastkey, firstkey, -1):
                logdict = self.get(i, appname=appname, die=False)
                if logdict:
                    if nrdone > maxitems:
                        return res
                    if lastid == logdict["id"]:
                        return res
                    res.append(logdict)
                    nrdone += 1
            return res

        nrdone = 0
        res = walk(appname, lastid)
        res.reverse()
        for logdict in res:
            args, nrdone = self.__do(method, logdict, epoch_from, epoch_to, args, nrdone)
        if len(res) > 1:
            lastid = res[-1]["id"]
        return args, lastid

    def __do(self, method, logdict, epoch_from, epoch_to, args, nrdone):
        if logdict["epoch"] < epoch_from:
            return args, nrdone
        if logdict["epoch"] > epoch_to:
            return args, nrdone
        nrdone += 1
        args2 = method(logdict, args=args)
        if args2:
            args = args2
        return args, nrdone

    def walk(self, method, id_from=None, time_from=None, time_to=None, maxitems=10000, appname=None, args={}):
        """

        def method(key,errorobj,args):
            return args

        will walk over all alerts, can manipulate or fetch that way


        :param method:
        :return:
        """
        if time_from:
            epoch_from = j.data.types.datetime.clean(time_from)
        if time_to:
            epoch_to = j.data.types.datetime.clean(time_to)
        else:
            epoch_to = j.data.time.epoch + 1

        if not appname:
            appname = j.application.appname

        nrdone = 1

        ids = self._data_container_ids_get_from_time(epoch_from=epoch_from, epoch_to=epoch_to, appname=appname)
        for container_id in ids:
            for logdict_json in self._data_container_get(container_id, appname=appname):
                # now we need to refine, so the timings are exact
                logdict = json.loads(logdict_json)
                if nrdone > maxitems:
                    return args
                if id_from:
                    if id_from > logdict["id"]:
                        # means id_from was specified, should only walk on items which are higher
                        # TODO: needs to be verified
                        continue
                args, nrdone = self.__do(method, logdict, epoch_from, epoch_to, args, nrdone)

        incrkey = "logs:%s:incr" % (appname)
        lastkey = int(self.db.get(incrkey))
        firstkey = lastkey - 2000

        for i in range(firstkey - 1, lastkey):
            logdict = self.get(i, appname=appname, die=False)
            if logdict:
                if nrdone > maxitems:
                    return args
                args, nrdone = self.__do(method, logdict, epoch_from, epoch_to, args, nrdone)

        return args

    def reset(self):
        self.db.delete(self._rediskey_alerts)
        self.db.delete(self._rediskey_logs)

    def tail_get(self, appname, maxitems=200, lastid=None):
        """

        :param appname:
        :param maxitems: maxitems to go back to in time
        :return: list of items, lastid
        """

        def do(logdict, args):
            args["res"].append(logdict)
            return args

        args = {}
        args["res"] = []
        args, lastid = self.walk_reverse(do, args=args, appname=appname, lastid=lastid, maxitems=maxitems)
        return args["res"], lastid

    def find(
        self,
        id_from=None,
        time_from=None,
        time_to=None,
        appname=None,
        cat=None,
        message=None,
        processid=None,
        context=None,
        file_path=None,
    ):
        """
        :param cat: filter against category (can be part of category)
        :param processid = pid = int
        :param: context (matches on any part of context)
        :param: message, checks in messagepub & message, can be part of the message
        :param: id_from, as used in walk function, will only starting finding from that position
        :param: file_path, filter on filepath, can be part of template args like {DIR_BASE} are supported
        :param message:
        :return: list([key,err])
        """
        # TODO: implement using walk (arguments above need to be passed as args to the walker method)
        res = []
        for res0 in self.list():
            key, err = res0
            found = True
            if message is not "" and err.message.find(message) == -1:
                found = False
            if cat is not "" and err.cat.find(cat) == -1:
                found = False
            if found:
                res.append([key, err])
        return res

    def tail(self, appname, maxitems=200, lastid=None, wait=True):
        """
        uses tail_get and prints to the screen
        :param appname:
        :param maxitems:
        :param lastid:
        :param wait:
        :return:
        """
        while True:
            res, lastid = self.tail_get(appname=appname, maxitems=maxitems, lastid=lastid)
            if len(res) > 0:
                for ld in res:
                    j.core.tools.log2stdout(ld)
            else:
                time.sleep(0.1)

            if not wait:
                return res

    def count(self):
        return len(self.list())

    def print(
        self,
        id_from=None,
        time_from=None,
        time_to=None,
        appname=None,
        cat=None,
        message=None,
        processid=None,
        context=None,
        file_path=None,
    ):
        """
        print on stdout the records which match the arguments

        :param cat: filter against category (can be part of category)
        :param processid = pid = int
        :param: context (matches on any part of context)
        :param: message, checks in messagepub & message, can be part of the message
        :param: id_from, as used in walk function, will only starting finding from that position
        :param: file_path, filter on filepath, can be part of template args like {DIR_BASE} are supported
        :param message:
        :return: list([key,err])
        """
        for (key, obj) in self.find(...):
            raise RuntimeError("todo")

        # tb_text = obj.trace
        # j.core.errorhandler._trace_print(tb_text)
        # print(obj._hr_get(exclude=["trace"]))
        # print("\n############################\n")
