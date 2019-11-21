from Jumpscale import j
import copy

JSBASE = j.application.jsbase_get_class()

SCHEMA_ALERT = """
@url = jumpscale.alerthandler.alert
level = 0
message = ""
message_pub = ""
cat = ""
trace= ""
time_first = (D)
time_last = (D)
count = 0
"""


class AlertHandler(j.baseclasses.object):

    __jslocation__ = "j.tools.alerthandler_redis"

    def _init(self, **kwargs):

        if not j.application.schemas:
            raise j.exceptions.Base("cannot use alerthandler because digital me has not been installed")
        self.schema_alert = j.data.schema.schema_add(SCHEMA_ALERT)

        self.db = j.core.db
        self.serialize_json = True

    def log(self, error, tb_text=""):
        """
        :param error: is python exception (can be from jumpscaleX_core/Jumpscale/errorhandling/JSExceptions.py)
        :return: jumpscale.alerthandler.alert object
        """
        e = self.schema_alert.new()
        e.time_first = j.data.time.epoch
        if "trace_do" in error.__dict__:
            # this are exceptions we raised from errorhandling/JSExceptions.py
            e.message = error.message
            e.message_pub = error.message_pub
            if error.cat is not "":
                e.cat = error.cat
            else:
                name = str(error.__class__).split("'")[1].strip()
                e.cat = "js.error.%s" % name
            e.level = error.level
            e.trace = error.trace
        else:
            args = [str(item) for item in error.args]
            e.message = "\n".join(args)
            name = str(error.__class__).split("'")[1].strip()
            e.cat = "python.%s" % name
        e.trace = tb_text

        key_input = j.core.text.pad("%s_%s_%s" % (e.cat, e.level, e.message), 150)
        key_input = key_input.strip()
        key_input = j.core.text.strip_to_ascii_dense(key_input)
        key = "alerts:%s" % j.data.hash.md5_string(key_input)

        e2 = self.get(key, die=False)
        if e2 is not None:
            e = e2  # use the data from DB

        e.count += 1
        e.time_last = j.data.time.epoch

        self.set(key, e)
        return e

    def set(self, key, err):
        if self.serialize_json:
            self.db.set(key, err._json, ex=24 * 3600)  # expires in 24h
        else:
            self.db.set(key, err._data, ex=24 * 3600)  # expires in 24h

    def get(self, key, new=False, die=True):
        res = self.db.get(key)
        if res is None:
            if die == False:
                return
            if new:
                return self.schema_alert.new()
        # now we have unique key only using part of message, cat & level
        else:
            if res[0] == 123:  # means is 99999/100000 json, hope goes well (-:
                res2 = j.data.serializers.json.loads(res)
                e = self.schema_alert.get(data=res2)
            else:
                e = self.schema_alert.get(data=res)
            return e

    def delete(self, key):
        self.db.delete(key)

    def walk(self, method, args={}):
        """

        def method(key,errorobj,args):
            return args

        will walk over all alerts, can manipulate or fetch that way

        :param method:
        :return:
        """
        for key in self.db.keys("alerts:*"):
            obj = self.get(key)
            args = method(key, obj, args)
        return args

    def reset(self):
        def delete(key, err, args):
            self.db.delete(key)

        args = self.walk(delete, args={"res": []})
        return args

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
        js9 'j.tools.alerthandler.print()'
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

        if delete:
            self.reset()

            assert self.count() == 0

        for i in range(10):
            try:
                2 / 0
            except Exception as e:
                j.errorhandler.try_except_error_process(e, die=False)  # if you want to continue

        error = j.exceptions.HaltException(
            "halt test"
        )  # this test will not have nice stacktrace because is not really an exception

        j.errorhandler.try_except_error_process(error, die=False)

        if delete:
            assert self.count() == 2

        print(j.tools.alerthandler.list())

        j.tools.alerthandler.print()

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
