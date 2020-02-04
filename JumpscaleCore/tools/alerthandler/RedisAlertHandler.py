from Jumpscale import j

try:
    import ujson as json
except BaseException:
    import json


SCHEMA_ALERT = """
@url = jumpscale.alerthandler.alert
0 : alert_id = 0 (I)
1 : identifier = "" (S)               #unique identification for the alert,is hash of alert_type+message+message_pub+cat
2 : alert_type = "bug,question,event_system,event_monitor,event_operator" (E)
3 : level = 0
4 : message = ""
5 : message_pub = ""                  #optional public message
6 : cat = ""                          #a freely chosen category can be in dot notation e.g. performance.cpu.high
7: count = 0 (I)
8: status = "closed,new,open,reopen" (E)
9: time_first = (D)
10: time_last = (D)
11: support_trace = (LO) !jumpscale.alerthandler.alert.support.trace
12: events = (LO) !jumpscale.alerthandler.alert.event
13: tracebacks = (LO) !jumpscale.alerthandler.alert.traceback
# 14: logs = (LO) !jumpscale.alerthandler.alert.log

@url = jumpscale.alerthandler.alert.support.trace
0 : support_severity = "info,minor,normal,high,critical" (E)        #set by operator
1 : support_status = "closed,new,open,troubleshoot,ignore" (E)
2 : support_assigned = ""                                           #optional support operator who takes responsiblity
3 : support_comment = ""

#is an event of the alert
@url = jumpscale.alerthandler.alert.event
0 : threebot_name =  (S)            #threebot names, can be more than 1
1 : process_ids = (LI)              #the process id if known, can be more than one because can happen in more than 1 process
2 : code_path = ""
3 : code_line = ""
4 : code_line_nr = 0
5 : count = 0 (I)
6 : time_first = (D)
7 : time_last = (D)
8 : trace= "" (S)
9 : data = (S)

# #optional log items
# #in line with threefoldtech/jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md
# @url = jumpscale.alerthandler.alert.log
# 0 : threebot_name =  (S)            #threebot names, can be more than 1
# 1 : process_id = (I)                #the process id if known
# 2 : logs = (LO) !jumpscale.alerthandler.alert.logitem
#
# @url = jumpscale.alerthandler.alert.logitem
# 0 : filepath = ""
# 1 : linenr = (I)
# 2 : message = ""
# 3 : level = (I)
# 4 : context = (S)
# 5 : cat = (S)
# 6 : data = (S)

#optional tracebacks
@url = jumpscale.alerthandler.alert.traceback
0 : threebot_name =  (S)            #threebot names, can be more than 1
1 : process_id = (I)                #the process id if known
2 : items = (LO) !jumpscale.alerthandler.alert.tracebackitem

@url = jumpscale.alerthandler.alert.tracebackitem
0 : filepath = ""
1 : linenr = (I)
2 : line = ""
3 : context = ""


"""

# ## log (error) levels
# - CRITICAL 	50
# - ERROR 	40
# - WARNING 	30
# - INFO 	    20
# - STDOUT 	15
# - DEBUG 	10

import redis


class AlertHandler(j.baseclasses.object):

    __jslocation__ = "j.tools.alerthandler"

    def _init(self, **kwargs):

        self.schema_alert = j.data.schema.get_from_text(SCHEMA_ALERT)

        self.db = redis.Redis()
        self.serialize_json = True
        self._rediskey_alerts = "alerts"
        self._rediskey_logs = "logs:%s" % (self._threebot_name)

    def setup(self):
        if self.handle_error not in j.errorhandler.handlers:
            j.errorhandler.handlers.append(self.handle_error)

    def _process_logdict(self, logdict):
        if "processid" not in logdict or not logdict["processid"] or logdict["processid"] == "unknown":
            logdict["processid"] = j.application.systempid
        return logdict

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

    def _loads(self, s):
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")

        assert isinstance(s, str)
        try:
            return json.loads(s)
        except Exception as e:
            raise RuntimeError("Cannot load json\n%s\n%s" % (s, e))

    def handle_error(self, logdict):
        j.application.inlogger = True
        try:
            self._handle_error(logdict)
        except Exception as e:
            print("**ERROR IN ERROR HANDLER**")
            print(str(e))
        j.application.inlogger = False

    def alert_raise(self, message, message_pub, cat="", level=20, alert_type="event_operator"):
        logdict = {}
        logdict["message"] = message
        logdict["message_pub"] = message_pub
        logdict["cat"] = cat
        logdict["level"] = level
        logdict["alert_type"] = alert_type
        self._handle_error(logdict)

    def get_identifier(self, msg, msg_pub, cat, alert_type):
        if cat is None:
            cat = ""
        if alert_type is None:
            alert_type = "event_system"
        return j.data.hash.md5_string("_".join([msg, msg_pub, cat, alert_type]))

    def _handle_error(self, logdict):
        """handle error

        :param logdict: logging dict (see jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md for keys)
        :type logdict: dict
        """

        logdict = self._process_logdict(logdict)

        alert_type = "event_system"

        if "cat" not in logdict:
            logdict["cat"] = ""
        if "public" not in logdict:
            logdict["public"] = ""

        identifier = self.get_identifier(logdict["message"], logdict["public"], logdict["cat"], alert_type)
        alert = self.get(identifier=identifier, die=None)

        if alert.status == "new":
            alert.status = "open"
        if alert.status == "closed":
            alert.status = "reopen"

        alert.identifier = identifier
        alert.alert_type = alert_type
        alert.level = logdict["level"]
        alert.message = logdict["message"]
        alert.message_pub = logdict["public"]
        alert.cat = logdict["cat"]
        alert.count += 1

        if not alert.time_first:
            alert.time_first = j.data.time.epoch
        alert.time_last = j.data.time.epoch

        self._add_event_from_logdict(alert, logdict)

        self.set(alert)

    def _event_get(self, alert, threebot_name=None):
        if not threebot_name:
            threebot_name = self._threebot_name
        for event in alert.events:
            if event.threebot_name == threebot_name:
                return event
        return alert.events.new()

    @property
    def _threebot_name(self):
        try:
            tname = j.tools.threebot.me.default.tname
        except:
            tname = "unknown"
        return tname

    def _add_event_from_logdict(self, alert, logdict, threebot_name=None):

        if not threebot_name:
            threebot_name = self._threebot_name

        threebot_name = threebot_name.lower().strip()

        if len(alert.events) > 20:
            alert.events.pop(0)

        event = self._event_get(alert, threebot_name=threebot_name)

        event.threebot_name = threebot_name

        if "processid" in logdict:
            pid = logdict["processid"]
            if len(event.process_ids) > 20:
                event.process_ids.pop(0)
            if pid not in event.process_ids:
                event.process_ids.append(pid)

        if "filepath" in logdict:
            code_path = logdict["filepath"]
            if "sandbox/" in code_path:
                code_path = "{DIR_BASE}/%s" % code_path.split("sandbox/", 1)[1]
        else:
            code_path = ""

        event.code_path = code_path
        event.code_line = ""  # TODO:
        if "linenr" in logdict:
            event.code_line_nr = logdict["linenr"]

        event.count += 1

        if not event.time_first:
            event.time_first = j.data.time.epoch
        event.time_last = j.data.time.epoch

        if "traceback" in logdict and logdict["traceback"]:

            self._trace_add(alert, logdict["traceback"], threebot_name=threebot_name, process_id=logdict["processid"])

            # event.trace = j.core.tools.traceback_format(logdict["traceback"])

        if "data" in logdict:
            data = self._dumps(logdict["data"])
            event.data = data

    def _trace_add(self, alert, traceback_list, threebot_name, process_id):
        if len(alert.tracebacks) > 5:
            alert.tracebacks.pop(0)
        tbgroup = alert.tracebacks.new()
        tbgroup.process_id = process_id
        tbgroup.threebot_name = threebot_name
        for item in traceback_list:
            filepath = item[0]
            context = item[1]
            if context in ["<module>"]:
                continue
            linenr = item[2]
            line = item[3]
            # 0 : filepath = ""
            # 1 : linenr = (I)
            # 2 : line = ""
            # 3 : context = ""
            r = tbgroup.items.new()
            if "sandbox/" in filepath:
                filepath = "{DIR_BASE}/%s" % filepath.split("sandbox/", 1)[1]
            r.filepath = filepath
            r.linenr = linenr
            r.line = line
            r.context = context

    def set(self, alert):
        data = self._dumps(alert._ddict)
        res = self.db.hset(self._rediskey_alerts, alert.identifier, data)

    # def set(self, key, err):
    #     if self.serialize_json:
    #         self.db.set(key, err._json, ex=24 * 3600)  # expires in 24h
    #     else:
    #         self.db.set(key, err._data, ex=24 * 3600)  # expires in 24h

    def get(self, identifier, die=False):
        res = self.db.hget(self._rediskey_alerts, identifier)
        if not res:
            if die:
                raise RuntimeError("could not find alert with identifier:%s" % identifier)
            return self.schema_alert.new()
        datadict = self._loads(res)
        alert = self.schema_alert.new(datadict=datadict)
        return alert

    def delete(self, identifier):
        """delete an alert

        :param identifier: alert unique identifier
        :type identifier: str
        :return: 1 or 0 (if it was not already there)
        :rtype: int
        """
        return self.db.hdel(self._rediskey_alerts, identifier)

    def delete_all(self):
        """
        delete all alerts
        """
        self.db.delete(self._rediskey_alerts)

    def walk(self, method, args={}):
        """

        def method(key,errorobj,args):
            return args

        will walk over all alerts, can manipulate or fetch that way

        :param method:
        :return:
        """
        for key in self.db.hkeys(self._rediskey_alerts):
            obj = self.get(key)
            args = method(key, obj, args)
        return args

    def reset(self):
        self.db.delete(self._rediskey_alerts)
        self.db.delete(self._rediskey_logs)

    def list(self):
        """
        :return: list([key,err])
        """

        def llist(key, err, args):
            args["res"].append([key, err])
            return args

        args = self.walk(llist, args={"res": []})
        return args["res"]

    def find(self, cat="", message=""):
        """
        :param cat: filter against category (can be part of category)
        :param message:
        :return: list([key,err])
        """
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

    def count(self):
        return len(self.list())

    def print(self):
        """
        kosmos 'j.tools.alerthandler.print()'
        """

        for (key, obj) in self.list():
            tb_text = obj.trace
            j.core.errorhandler._trace_print(tb_text)
            print(obj._hr_get(exclude=["trace"]))
            print("\n############################\n")

    def test(self, delete=True):
        """
        kosmos 'j.tools.alerthandler.test()'
        :return:
        """

        self.setup()

        if delete:
            self.reset()
            assert self.count() == 0

        for x in range(100):
            message = "random message %s" % x
            self.alert_raise(message=message, message_pub="", cat="color.red", level=20, alert_type="event_operator")

        x = 4
        message = "random message %s" % x
        self.alert_raise(message=message, message_pub="", cat="color.red", level=20, alert_type="event_operator")

        self.list()

        self._logger_enable()
        self._log_debug("this is a test")
        self._log_info("info", data={"a": 1, "b": 2}, cat="color.red")
        self._log_info("warning")

        for i in range(10):
            try:
                2 / 0
            except Exception as e:
                j.errorhandler.exception_handle(e, die=False)  # if you want to continue

        error = j.exceptions.Input(
            "halt test"
        )  # this test will not have nice stacktrace because is not really an exception

        j.errorhandler.exception_handle(error, die=False)

        if delete:
            assert self.count() == 102

        print(j.tools.alerthandler.list())

    # DO NOT REMOVE, can do traicks later with the eco.lua to make faster
    # def redis_enable(self):
    #     luapath = "%s/errorhandling/eco.lua" % j.dirs.JSLIBDIR
    #     lua = j.sal.fs.readFile(luapath)
    #     self._escalateToRedisFunction = j.core.db.register_script(lua)
    #     self._scriptsInRedis = True
    #
    # def _send2Redis(self, eco):
    #     if self.escalateToRedis:
    #         self._registerScrips()
    #         data = eco.json
    #         res = self._escalateToRedisFunction(
    #             keys=["queues:eco", "eco:incr", "eco:occurrences", "eco:objects", "eco:last"], args=[eco.key, data])
    #         res = j.data.serializers.json.loads(res)
    #         return res
    #     else:
    #         return None
