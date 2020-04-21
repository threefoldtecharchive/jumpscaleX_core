import redis

try:
    import ujson as json
except BaseException:
    import json

from Jumpscale import j


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
9: time_first = (T)
10: time_last = (T)
11: support_trace = (LO) !jumpscale.alerthandler.alert.support.trace
12: events = (LO) !jumpscale.alerthandler.alert.event
13: tracebacks = (LO) !jumpscale.alerthandler.alert.traceback
14: logs = (LO) !jumpscale.alerthandler.alert.log   #should only keep e.g. last 5 instances per threebot
15: appname = "" (S)

@url = jumpscale.alerthandler.alert.support.trace
0 : support_severity = "info,minor,normal,high,critical" (E)        #set by operator
1 : support_status = "closed,new,open,troubleshoot,ignore" (E)
2 : support_assigned = ""                                           #optional support operator who takes responsiblity
3 : support_comment = ""
4:  modtime = (T)

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

@url = jumpscale.alerthandler.alert.log
0 : threebot_name =  (S)            #threebot names, can be more than 1
1 : app_name = (S)                  #allows us to find the log back
2 : latest_logid = (I)              #latest logid

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

# log (error) levels
LEVELS = {50: "CRITICAL", 40: "ERROR", 30: "WARNING", 20: "INFO", 15: "STDOUT", 10: "DEBUG"}

skip = j.baseclasses.testtools._skip


class AlertHandler(j.baseclasses.object):

    __jslocation__ = "j.tools.alerthandler"

    def _init(self, **kwargs):

        self.schema_alert = j.data.schema.get_from_text(SCHEMA_ALERT)

        self.db = redis.Redis()
        self.serialize_json = True
        self._rediskey_alerts = "alerts"
        self._rediskey_alerts_id = "alertsid"
        self._rediskey_alerts_ids = "alertsids"
        # self._rediskey_logs = "logs:%s" % (self._threebot_name)

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
        self._handle_error(logdict)
        # prob better to always die
        # try:
        #     self._handle_error(logdict)
        # except Exception as e:
        #     print("**ERROR IN ERROR HANDLER**")
        #     print(str(e))
        j.application.inlogger = False

    def alert_raise(self, message, message_pub, cat="", level=20, alert_type="event_operator"):
        logdict = {}
        logdict["message"] = message
        logdict["public"] = message_pub
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
        alert.message = j.core.tools.text_replace(logdict["message"])
        alert.message_pub = logdict["public"]
        alert.cat = logdict["cat"]
        alert.count += 1
        alert.appname = j.application.appname

        if not alert.time_first:
            alert.time_first = j.data.time.epoch
        alert.time_last = j.data.time.epoch

        # add the link to the logs at that point, allows to retrieve info later
        if len(alert.logs) > 10:
            alert.logs.pop(-1)

        l = alert.logs.new()
        l.latest_logid = j.core.myenv.loghandler_redis.last_logid
        l.threebot_name = self._threebot_name
        l.app_name = j.application.appname

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
            tname = j.myidentities.me.tname
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
        if not alert.alert_id:
            alert.alert_id = self.db.incr(self._rediskey_alerts_id)
            self.db.hset(self._rediskey_alerts_ids, alert.alert_id, alert.identifier)

        data = self._dumps(alert._ddict)
        res = self.db.hset(self._rediskey_alerts, alert.identifier, data)

    def get(self, identifier=None, alert_id=None, die=False, new=True):
        if alert_id:
            identifier = self.db.hget(self._rediskey_alerts_ids, alert_id)
            if not identifier:
                if die:
                    raise RuntimeError("could not find alert with id:%s" % alert_id)
                return None
        res = self.db.hget(self._rediskey_alerts, identifier)
        if not res:
            if die:
                raise RuntimeError("could not find alert with identifier:%s" % identifier)
            if new:
                return self.schema_alert.new()
            else:
                return None
        datadict = self._loads(res)
        alert = self.schema_alert.new(datadict=datadict)
        return alert

    def delete(self, alert):
        """delete an alert

        :param identifier: alert unique identifier
        :type identifier: str
        :return: 1 or 0 (if it was not already there)
        :rtype: int
        """
        assert isinstance(alert, self.schema_alert.objclass())
        self.db.hdel(self._rediskey_alerts_ids, alert.alert_id)
        self.db.hdel(self._rediskey_alerts, alert.identifier)

    def delete_all(self):
        """
        delete all alerts
        """
        self.db.delete(self._rediskey_alerts)
        self.db.delete(self._rediskey_alerts_ids)
        self.db.delete(self._rediskey_alerts_id)
        self.db.delete("alertslast")

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
        # self.db.delete(self._rediskey_logs)

    def list(self):
        """
        :return: list([key,err])
        """

        def llist(key, err, args):
            args["res"].append([key, err])
            return args

        args = self.walk(llist, args={"res": []})
        return args["res"]

    def find(self, cat="", message="", pid=None, time_from=None, time_to=None, appname=None):
        """filter alerts by cat, message, pid or time
        :param cat: category, defaults to ""
        :type cat: str, optional
        :param message: message (can be public message too), defaults to ""
        :type message: str, optional
        :param pid: process id, defaults to None
        :type pid: int, optional
        :param time_from: alert.time_last needs to be > than specified time_from example -4h
        :param time_to: alert.time_last needs to be < than specified time_from example -1h
        :return: list of alert objects
        :rtype: list
        """
        res = []
        cat = cat.strip().lower()
        message = message.strip().lower()

        time_from = j.data.types.datetime.clean(time_from)
        time_to = j.data.types.datetime.clean(time_to)

        for _, alert in self.list():
            found = True

            if message:
                if not message in alert.message.strip().lower() and not message in alert.message_pub.strip().lower():
                    found = False

            if cat:
                if not cat in alert.cat.strip().lower():
                    found = False

            if appname:
                if alert.appname.lower().find(appname) == -1:
                    found = False

            if pid:
                found2 = False
                for event in alert.events:
                    if pid in event.process_ids:
                        found2 = True
                if not found2:
                    found = False

            if time_to or time_from:
                found2 = False
                if time_to and time_from:
                    if int(time_from) <= alert.time_last <= int(time_to):
                        found2 = True
                elif time_to:
                    if alert.time_last <= int(time_to):
                        found2 = True
                elif time_from:
                    if int(time_from) <= alert.time_last:
                        found2 = True
                if not found2:
                    found = False

            if found:
                res.append(alert)

        return res

    def count(self):
        return len(self.list())

    def format_traceback(self, traceback):
        """format a single traceback

        :param traceback: traceback object
        :type traceback: jumpscale.alerthandler.alert.traceback
        :return: formatted traceback as a string with colors
        :rtype: str
        """
        tb_list = []
        for item in traceback.items:
            tb_list.append((item.filepath, item.context, item.linenr, item.line, {}))
        return j.core.tools.traceback_format(tb_list)

    def alert_print(self, alert, exclude=None, show_tb=True):
        """print alert information
        :param alert: alert object
        :type alert: jumpscale.alerthandler.alert
        :param exclude: property names to exclude
        :type exclude: list of str, optional
        :param show_tb: if set, tracebakcs will be printed too, defaults to True
        :type show_tb: bool, optional
        """
        if not exclude:
            exclude = []

        exclude += ["support_trace", "events", "tracebacks"]

        props = alert._ddict_hr_get(exclude=exclude)
        props["level"] = LEVELS.get(int(props["level"]), "Unknown")
        print(alert._hr_get_properties(props))

        if show_tb:
            for tb in alert.tracebacks:
                if tb.items:
                    print(f"Traceback (PID: {tb.process_id}, 3bot: {tb.threebot_name})")
                    print(self.format_traceback(tb))

    def alerts_print(self, alerts):
        """
        print alerts
        with date, count, identifier and message

        :param alerts: list of alert objects
        :type alerts: list of Alert
        """
        exclude = ["alert_id", "cat", "message_pub", "alert_type"]
        for alert in alerts:
            self.alert_print(alert, exclude=exclude, show_tb=False)

    def alerts_list(self, alerts):

        for alert in alerts:
            print(self._alert_oneline(alert))

    def _alert_oneline(self, alert):
        time_first_hr = j.data.types.datetime.toHR(alert.time_last)
        if len(alert.message_pub) > 10:
            msg = alert.message_pub
        else:
            msg = alert.message.replace("\n", " ").replace("EXCEPTION:", " ").replace("EXCEPTION:", "  ")
        msg2 = j.core.text.toAscii(msg, 120)
        return f" {alert.appname:<20} {time_first_hr:<15} . {alert.alert_id:<5}: {msg2:<100} "

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
        print("TEST OK")

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
