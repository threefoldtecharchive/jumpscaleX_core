from Jumpscale import j


from gevent import queue
from gevent import spawn
import inspect


JSBASE = j.baseclasses.object


class ServiceBase2(j.baseclasses.object):

    _MODEL = None

    def _input_error_exit(self, msg, category=""):
        """
        is just a test method with content inside
        """

        def sss(id=None, name=None, asker_dmid=None):

            JSBASE.__init__(self)

            if self.__class__._MODEL is None:
                self.__class__._MODEL = "just something"

            self._state = None

        def data(self):

            if self._data is None:
                # self.id = id
                j.shell()

        if self.__class__._MODEL is None:
            self.__class__._MODEL = j.world.system._bcdb.model_get(schema=self.__class__._SCHEMA_TXT)

        self._state = None

        self.id = id
        self._running = None

    def __init__(self, id=None, name=None, asker_dmid=None):

        pass

        JSBASE.__init__(self)

        # self._state = None
        #
        # self.id = id
        # if name is not None or asker_dmid is not None:
        #     self.name=name
        # else:
        #     self._data = None
        # self._running = None

    @property
    def data(self):

        if self._data is None:
            # self.id = id
            j.shell()

    @property
    def state(self):

        if self._state is None:
            if self.id is None:
                self._input_error_exit("id should not be None")
            j.shell()

    def service_unmanage(self):

        j.shell()

    def service_manage(self):
        """
        get the service to basically run in memory, means checking the monitoring, make the model reality...
        :return:
        """
        if self._running is None:
            self.q_in = queue.Queue()
            self.q_out = queue.Queue()
            self.task_id_current = 0
            self.greenlet_task = spawn(self._main)
            # spawn(self._main)

            for method in inspect.getmembers(self, predicate=inspect.ismethod):
                j.shell()
                w
                mname = method[0]
                print("iterate over method:%s" % mname)

                if mname.startswith("monitor"):
                    if mname in ["monitor_running"]:
                        continue
                    print("found monitor: %s" % mname)
                    method = getattr(self, mname)
                    self.monitors[mname[8:]] = spawn(method)
                else:
                    if mname.startswith("action_"):
                        self._stateobj_get(mname)  # make sure the action object exists

    def _main(self):
        self._log_info("%s:mainloop started" % self)
        # make sure communication is only 1 way
        # TODO: put metadata
        while True:
            action, data = self.q_in.get()
            self._log_info("%s:action:%s:%s" % (self, action, data))
            method = getattr(self, action)
            res = method(data)
            print("main res:%s" % res)
            self.q_out.put([0, res])

    def _stateobj_get(self, name):
        for item in self.data.stateobj.actions:
            if item.name == name:
                return item
        a = self.data.stateobj.actions.new()
        a.name = name

    def _coordinator_action_ask(self, name):
        arg = None
        cmd = [name, arg]
        self.q_in.put(cmd)
        rc, res = self.q_out.get()
        return rc, res

    @property
    def _name(self):
        return self.data.name

    @property
    def _instance(self):
        return self.data.instance
