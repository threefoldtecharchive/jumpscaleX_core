import os
from Jumpscale import j
import gipc
import gevent

JSConfigClient = j.baseclasses.object_config


class GIPCProcess(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.servers.gipc.process.1
           name** = "default" (S)
           start = (T)
           end = (T)
           kwargs= (dict)
           state= "init,started,ok,error" (E)
           """

    def _init(self, **kwargs):
        self.nosave = True
        self.process = None
        self.greenlet = None

    def _bcdb(self):
        return j.application.bcdb_system

    def start(self):
        self.greenlet = gevent.spawn(self._start)

    def _start(self):
        """
        """
        self._log_info("start process", data=self._data)
        kw = {}
        for key, val in self.kwargs:
            kw[key] = val
        self.process = gipc.start_process(target=self._method, kwargs=kw)
        self.state = "started"
        self.start = j.data.time.epoch
        r = self.process.join()
        if self.process.exitcode > 0:
            self.state = "error"
            self.end = j.data.time.epoch
            raise j.exceptions.Base("Could not run:%s" % self.name, data=self)
        else:
            self.state = "ok"
            self.end = j.data.time.epoch
        self._log_info("process ok", data=self._data)

    def wait(self, die=True):
        while True:
            if self.greenlet.dead == False and self.process.is_alive():
                gevent.time.sleep(0.05)
            else:
                if self.greenlet.dead:
                    if self.state == "ok":
                        return True
                    elif self.state == "error":
                        pass
                    else:
                        raise j.exceptions.Base("greenlet died:%s" % self.name)
                else:
                    gevent.time.sleep(0.05)
                if self.state == "error":
                    if die:
                        raise j.exceptions.Base("could not execute:%s" % self.name, data=self)
                    else:
                        self._log_error("could not execute:%s" % self.name, data=self)
                        return False
                return True
