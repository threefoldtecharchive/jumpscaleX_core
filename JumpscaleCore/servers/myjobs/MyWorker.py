from Jumpscale import j
from .MyWorkerProcess import MyWorkerProcess
import gipc
import sys


class MyWorker(j.baseclasses.object_config):
    _name = "worker"
    _SCHEMATEXT = """
        @url = jumpscale.myjobs.worker
        name**= ""
        timeout = 3600
        time_start = 0 (T)
        last_update = 0 (T)
        current_job = (I)
        error = "" (S)
        state** = "NEW,ERROR,BUSY,WAITING,HALTED" (E)
        pid = 0
        #if halt on True will stop
        halt = false (B)
        type = "tmux,subprocess,inprocess" (E)
        debug = false (B)
        nr = 0 (I)
        """

    def _init(self, **kwargs):
        # important to check (at least for now)
        assert self._bcdb.storclient._check_cat == "myjobs"
        if "nr" in kwargs:
            self.nr = kwargs["nr"]
            self.name = "w%s" % self.nr
        elif self.name.startswith("w"):
            try:
                self.nr = int(self.name[1:])
            except Exception as e:
                raise j.exceptions.JSBUG("need to be int after w")
        if not self.nr > 0 and self.nr < 20:
            raise j.exceptions.JSBUG(f"worker '{self.nr}' nr is not between 1 and 20 ")

    def _state_set_new(self):
        self.time_start = 0
        self.last_update = 0
        self.state = "NEW"
        self.pid = 0
        self.current_job = 2147483647
        self.halt = False

    def start(self):
        def state_update():
            self.state = "WAITING"
            self.time_start = j.data.time.epoch
            self.last_update = j.data.time.epoch
            self.current_job = 2147483647  # means none
            self.save()

        if self.type in ["TMUX"]:
            self._worker_start_tmux()
        elif self.type in ["SUBPROCESS"]:
            self._worker_subprocess_start()
        elif self.type in ["INPROCESS"]:
            state_update()
            self._worker_start_inprocess()
            self.stop()
        else:
            raise j.exceptions.JSBUG("did not find right type to start worker")
        state_update()

    def stop(self, hard=False):
        self.halt = True
        self.save()

        if hard:
            if self.type in ["TMUX"]:
                cmd = j.servers.startupcmd.get(name="workers_%s" % self.nr)
                cmd.stop(force=True)
            if self.type in ["INPROCESS"]:
                self._log_info("INPROCESS STOP")
                sys.exit(0)
            self.state = "HALTED"
            self.pid = 0
            self.last_update = j.data.time.epoch
            self.current_job = 2147483647
            self.halt = False
            self.save()

    def _worker_subprocess_start(self):
        worker = gipc.start_process(target=MyWorkerProcess, kwargs={"worker_id": self._id})
        j.servers.myjobs._workers_gipc[self._id] = worker

    def _worker_start_tmux(self, reset=False):
        """
        kosmos "j.servers.myjobs._workers_start_tmux(4)"

        :param: nr is the nr of the tmux session workers_$nr is the name

        """
        # j.builders.apps.corex.install()
        # j.servers.corex.default.start()  # starts corex at port 1500
        if not reset:
            self.load()
            if self.state in ["WAITING", "BUSY"]:
                if self.last_update > j.data.time.epoch - 40:
                    self._log_info("no need to start worker:%s" % self.nr)
                    return

        def start(nr):
            self._log_info("start worker:%s" % nr)
            cmd = j.servers.startupcmd.get(name="workers_%s" % nr)
            cmd.cmd_start = "j.servers.myjobs._worker_inprocess_start_from_tmux(%s)" % nr
            # COREX has still issues so fall back on tmux
            cmd.executor = "tmux"
            cmd.interpreter = "jumpscale_gevent"
            cmd.start(reset=True)

        start(self.nr)

        # was attempt to start with gipc but got some weird stuff
        # p = j.servers.gipc.schedule(start, nr=self.nr)

    def _worker_start_inprocess(self):
        """
        kosmos "j.servers.myjobs.worker_start_inprocess()"

        easy to debug the myworker framework because can see issues in the jobs executed

        will block our main process

        :return:
        """
        self.time_start = j.data.time.epoch
        self.last_update = j.data.time.epoch
        self._log_debug("worker in process: %s" % self._id, data=self._data)

        # model_worker = self._bcdb.model_get(url="jumpscale.myjobs.worker")

        MyWorkerProcess(worker_id=self._id, onetime=True, debug=self.debug)


class MyWorkers(j.baseclasses.object_config_collection):
    _name = "workers"

    _CHILDCLASS = MyWorker
