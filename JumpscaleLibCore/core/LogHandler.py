import json
import msgpack
from pathlib import Path
import time
import os


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class LogHandler:
    def __init__(self, myenv, db, appname=None):
        self._my = myenv
        self._tools = myenv.tools

        self.db = db
        if appname:
            self.appname = appname
        else:
            self.appname = "init"

        self.last_logid = 0

    def _process_logdict(self, logdict):
        if "processid" not in logdict or not logdict["processid"] or logdict["processid"] == "unknown":
            logdict["processid"] = os.getpid()

        if "epoch" not in logdict or not logdict["epoch"] or logdict["epoch"] == 0:
            logdict["epoch"] = int(time.time())

        return logdict

    @property
    def rediskey_logs(self):
        return "logs:%s:data" % (self.appname)

    @property
    def rediskey_logs_incr(self):
        return "logs:%s:incr" % (self.appname)

    def handle_log(self, logdict):
        """handle error

        :param logdict: logging dict (see jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md for keys)
        :type logdict: dict
        """

        if "traceback" in logdict:
            logdict.pop("traceback")

        rediskey_logs = self.rediskey_logs
        rediskey_logs_incr = self.rediskey_logs_incr

        if not self.db:
            return

        latest_id = self.db.incr(rediskey_logs_incr)

        self.last_logid = latest_id
        logdict["id"] = latest_id

        logdict = self._process_logdict(logdict)

        data = self._dumps(logdict)

        self.db.hset(rediskey_logs, latest_id, data)

        if latest_id / 1000 >= 2 and latest_id % 1000 == 0:
            # means we need to check and maybe do some cleanup, like this we only check this every 1000 items
            # only one log handler can have this, because id's are unique because of redis
            self._data_container_dump(latest_id)

    def _dumps(self, data):
        if isinstance(data, str):
            return data
        try:
            data = json.dumps(data, ensure_ascii=False, sort_keys=False, indent=True)
            return data
        except Exception as e:
            pass
        try:
            data = str(data)
        except Exception as e:
            data = "CANNOT SERIALIZE DATA"
        return data

    def _redis_get(self, identifier, appname=None, die=True):
        """
        returns json (is the format in redis)
        :param identifier:
        :param appname:
        :param die:
        :return:
        """
        if not appname:
            appname = self.appname
        rediskey_logs = "logs:%s:data" % appname

        if not self.db:
            return
        try:
            res = self.db.hget(rediskey_logs, identifier)
        except:
            raise RuntimeError("could not find log with identifier:%s" % identifier)

        if not res:
            if die:
                raise RuntimeError("could not find log with identifier:%s" % identifier)
            return
        return res

    def _data_container_dump(self, latest_id):
        startid = latest_id - 2000
        stopid = latest_id - 1000
        # TODO, need to verify, for the next 2000 logs items we will not have them all
        if msgpack:
            r = []
            # for redis which is 1 indexed
            for i in range(startid + 1, stopid + 1):
                d = self._redis_get(i)
                r.append(d)
            assert len(r) == 1000
            log_dir = self._tools.text_replace("{DIR_VAR}/logs")
            app_logs_path = "%s/%s" % (log_dir, self.appname)
            self._tools.dir_ensure(app_logs_path)
            path = "%s/%s/%s.msgpack" % (log_dir, self.appname, stopid)
            self._tools.file_write(path, msgpack.dumps(r))

            # rotate old msgpacks if we have logs > MAX_MSGPACKS_LOGS_COUNT (default: 50) file
            # means 50k logs, we delete the oldest 10 files, 10k logs
            msgpacks_count = self._my.config.get("MAX_MSGPACKS_LOGS_COUNT", 50)
            if len(os.listdir(app_logs_path)) > msgpacks_count + 1:
                all_files = sorted(Path(app_logs_path).iterdir(), key=os.path.getmtime)
                files_to_delete = all_files[: len(all_files) - msgpacks_count + 10]
                for file in files_to_delete:
                    self._tools.delete(file.as_posix())

        # now remove from redis
        keystodelete = []
        for key in self.db.hkeys(self.rediskey_logs):
            if int(key) < stopid + 1:
                keystodelete.append(key)

        for chunk in chunks(keystodelete, 100):
            self.db.hdel(self.rediskey_logs, *chunk)

    def _data_container_set(self, container, appname):
        if not msgpack:
            return
        assert isinstance(container, list)
        assert len(container) == 1000
        self._tools.shell()
        logdir = "%s/%s" % (self._log_dir, appname)
        if not self._tools.exists(logdir):
            return []
        else:
            data = msgpack.dumps(container)
            self._tools.shell()
            w
