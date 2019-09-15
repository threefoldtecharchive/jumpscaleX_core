from Jumpscale import j

import inspect
import os

try:
    import ujson as json
except:
    import json


class LoggerBase(j.baseclasses.object_config):
    """
    Handler to forward logs to a redis server
    send to the server

    ## dict keys:

    - processid : a string id can be a pid or any other identification of the log
    - cat   : optional category for log
    - level : levels see https://docs.python.org/3/library/logging.html#levels
    - linenr : nr in file where log comes from
    - filepath : path where the log comes from
    -
    - context : where did the message come from e.g. def name
    - message : content of the message
    - data : additional data e.g. stacktrace, depending context can be different
    - hash: optional, 16-32 bytes unique for this message normally e.g. md5 of eg. concatenation of important fields

    ### lOGGING LEVELS:

    - CRITICAL 	50
    - ERROR 	40
    - WARNING 	30
    - INFO 	    20
    - STDOUT    15
    - DEBUG 	10
    - NOTSET 	0


    """

    _SCHEMATEXT = """
        @url = jumpscale.tools.logger.1
        name** = ""
        stdout = False
        redis = False
        redis_addr = ""
        redis_port = 22
        redis_secret = ""
        level_min = 0
        filter_processid = "" (LS)
        filter_context= "" (LS)

        """

    def _init(self, **kwargs):
        self._reset()
        self._model.trigger_add(self._data_update_prop)

    @staticmethod
    def _data_update_prop(model, obj, kosmosinstance=None, action=None, propertyname=None):
        self = kosmosinstance  # this way code is same and can manipulate self like in other methods
        if propertyname:
            # this way we know that all will be reloaded
            # print("reset")
            self._reset()

    def _reset(self):
        self._redis_client_ = None
        self._inited = False

    def _init_at_log(self):
        """
        only called one time
        :return:
        """
        print("INITLOG")
        # put as std arguments, faster decision (NEEDS TO STAY!)
        if self.redis:
            self._redis = True
        else:
            self._redis = False
        if self.stdout:
            self._stdout = True
        else:
            self._stdout = False

        if self._redis:
            print("REDIS LUA LOADED")
            _dirpath = os.path.dirname(inspect.getfile(self.__class__))

            lua_path = "%s/log.lua" % _dirpath

            self._script = self._redis_client.storedprocedure_register("log", 0, lua_path)

        self._inited = True

    def _process(self, logdict):

        if not self._inited:
            self._init_at_log()

        if self._redis:

            record3 = json.dumps(logdict)

            self._script(args=[record3])

            # self._redis_client.storedprocedure_execute("log",record3)
            # self.redis_client.storedprocedure_debug("log","'%s'"%record3)

        if self._stdout and level > 14:
            self._process_stdout(logdict)

    def _process_stdout(self, logrecord):
        # can be overruled but default its done by installtools
        pass

    @property
    def _redis_client(self):
        if self._redis_client_ is None:
            self._redis_client_ = j.clients.redis.get(
                ipaddr=self.redis_addr, port=self.redis_port, password=self.redis_secret
            )

        return self._redis_client_
