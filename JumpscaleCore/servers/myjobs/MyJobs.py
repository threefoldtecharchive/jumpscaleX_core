import inspect
from Jumpscale import j
import gipc
import gevent
import time

from .MyWorker import MyWorker

JSBASE = j.baseclasses.object

schema_job = """
@url = jumpscale.myjobs.job
category*= ""
time_start = 0 (T)
time_stop = 0 (T)
state* = "NEW,ERROR,OK,RUNNING,HALTED" (E)
timeout = 0
action_id* = 0
args = (json)
kwargs = (dict)
result = (S)
error = (dict)
return_queues = (LS)


"""

schema_action = """
@url = jumpscale.myjobs.action
actorname = ""
methodname = ""
key* = ""  #hash
code = ""


"""

# NOT THE FASTEST WAY TO KEEP STATE OF WORKER BETWEEN THE PROCESSES, BUT EASY
schema_worker = """
@url = jumpscale.myjobs.worker
timeout = 3600
time_start = 0 (T)
last_update = 0 (T)
current_job = (I)
error = "" (S)
state* = "NEW"
pid = 0
halt = false (B)

"""


class MyJobs(JSBASE, j.application.JSFactoryTools):
    __jslocation__ = "j.servers.myjobs"

    def _init(self, **kwargs):
        self.queue_jobs_start = j.clients.redis.queue_get(redisclient=j.core.db, key="queue:jobs:start")
        self.queue_return = j.clients.redis.queue_get(redisclient=j.core.db, key="queue:jobs:return")
        self.workers = {}
        self.workers_nr_min = 1
        self.workers_nr_max = 10
        self.mainloop = None
        self.dataloop = None

        db = j.data.bcdb.get("myjobs", storclient=j.clients.rdb.client_get())

        self.model_job = db.model_get(schema=schema_job)
        self.model_action = db.model_get(schema=schema_action)
        self.model_worker = db.model_get(schema=schema_worker)

        self._init_ = False
        self.scheduled_ids = []

    def job_get(self, job_id):
        return self.model_job.get(job_id)

    def init(self, **kwargs):
        """
        activates the models and starts the worker manager if required
        """
        if self._init_ is False:

            if self.mainloop != None:
                self.mainloop.kill()

            if self.dataloop != None:
                self.dataloop.kill()

            self._init_ = True

    def action_get(self, key, return_none_if_not_exist=False):
        self.init()
        res = self.model_action.find(key=key)
        if len(res) > 0:
            o = self.model_action.get(res[0].id)
            return False, o
        else:
            if return_none_if_not_exist:
                return
            o = self.model_action.new()
            return True, o

    @property
    def workers_count(self):
        return len(self.workers.values())

    def start(self, debug=False, fixed_workers=None, subprocess=False):
        """

        kosmos -p "j.servers.myjobs.start()"
        kosmos -p "j.servers.myjobs.start(debug=True)"
        kosmos -p "j.servers.myjobs.start(debug=True,fixed_workers=10)"

        if non debug and fixed workers is None:
            always in subprocess, cannot see the output
            will add worker(s) when needed, when there is more work

        to test can but debug on True and run in separate console

        :return:
        """

        # self.init()
        if not debug:
            if not fixed_workers:
                self.mainloop = gevent.spawn(self._main_loop, subprocess)
            else:
                self._main_loop_fixed(nr=fixed_workers, debug=debug)  # does not wait, no need to do in gevent
        self.dataloop = gevent.spawn(self._data_loop)  # returns the data
        if debug:
            j.tools.logger.debug = True
            if not fixed_workers:
                self._main_loop()
            else:
                self._main_loop_fixed(nr=fixed_workers, debug=debug)

    def worker_start(self, onetime=False, subprocess=True, worker_id=None, debug=False):
        self.init()
        if onetime:
            subprocess = False
        if worker_id:
            w = self.model_worker.get(worker_id)
        else:
            w = self.model_worker.new()
            w.time_start = j.data.time.epoch
            w.last_update = j.data.time.epoch
            w = self.model_worker.set(w)
        self._log_debug("worker add: %s" % w.id, data=w._data)
        if subprocess:
            worker = gipc.start_process(target=MyWorker, kwargs={"worker_id": w.id})
            self.workers[w.id] = worker
        else:
            MyWorker(worker_id=w.id, onetime=onetime, debug=debug)
            # will make sure the data comes back
            self._data_process_untill_empty(timeout=5, die=False)

    def dataloop_start(self):
        if not self.dataloop:
            self.dataloop = gevent.spawn(self._data_loop)

    def workers_start_tmux(self, nrworkers=3, debug=False):
        """
        kosmos "j.servers.myjobs.workers_start_tmux(1)"
        """
        # j.builders.apps.corex.install()
        # j.servers.corex.default.start()  # starts corex at port 1500

        for nr in range(nrworkers):
            cmd = j.servers.startupcmd.get(name="workers_%s" % nr)
            if debug:
                cmd.cmd_start = "j.servers.myjobs.worker_start(subprocess=False,debug=True)"
            else:
                cmd.cmd_start = "j.servers.myjobs.worker_start(subprocess=False,debug=False)"
            # COREX has still issues so fall back on tmux
            cmd.executor = "tmux"
            cmd.interpreter = "jumpscale"
            cmd.start(reset=True)

        self.dataloop_start()

        self._log_info("visit http://localhost:1500/ for seeing the corex webscreen")

    def worker_start_inprocess(self, worker_id=None):
        """
        kosmos "j.servers.myjobs.worker_start_inprocess()"

        easy to debug the myworker framework because can see issues in the jobs executed

        :return:
        """
        self.worker_start(subprocess=False, worker_id=worker_id)

    def _data_loop(self):
        while True:
            self._log_debug("data_process run")
            self._data_process_1time(timeout=1)

    def _data_process_1time(self, timeout=0, die=False):
        r = self.queue_return.get(timeout=timeout)
        if r == None:
            return

        thedata = j.data.serializers.json.loads(r)  # change to json

        cat, objid, data = thedata

        if cat == "W":
            worker = self.model_worker.new(data=data)
            worker.id = objid
            worker.save()
            return True
        elif cat == "J":
            job = self.model_job.new(data=data)
            job.id = objid
            job.save()
            for queue_name in job.return_queues:
                queue = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % queue_name)
                queue.put(job.id)
            return True
        elif cat == "E":
            datae = j.data.serializers.json.loads(data)
            j.core.tools.log2stdout(datae)
            if die:
                raise j.exceptions.Base(data=datae)
            return True
        else:
            raise j.exceptions.Base("return queue does not have right obj")

    def _data_process_untill_empty(self, timeout=1, die=True):
        self.init()
        # need to wait till first one comes
        r = self._data_process_1time(timeout=timeout, die=die)
        if not r:
            return

        while r is not None:
            if self.queue_return.empty:
                return
            r = self._data_process_1time(timeout=timeout, die=die)

    def _main_loop_fixed(self, nr=10, debug=False):
        """
        will not dynamically allocate the workers, will be a fixed pool
        :param nr:
        :param debug:
        :return:
        """

        for i in range(nr):
            self.worker_start()
        if debug:
            j.shell()

    def _main_loop(self, subprocess=True):
        self._log_debug("monitor start")

        def test_workers_more():
            workers_count = self.workers_count
            a = workers_count < self.workers_nr_max
            b = workers_count < self.queue_jobs_start.qsize() or workers_count < self.workers_nr_min
            return a and b

        def test_workers_less():
            workers_count = self.workers_count
            a = workers_count > self.workers_nr_max
            b = workers_count > self.queue_jobs_start.qsize() and workers_count > self.workers_nr_min
            return a or b

        while True:

            self._log_debug("monitor run")

            # #there is already 1 working, lets give 2 sec time before we start monitoring
            # gevent.sleep(2)

            # TEST for timeout
            wids = [key for key in self.workers.keys()]
            for wid in wids:
                if wid in self.workers:
                    gproc = self.workers[wid]
                else:
                    continue
                if gproc.exitcode != None:
                    raise j.exceptions.Base("subprocess should never have been exitted")
                w = self.model_worker.get(wid)
                if w == None:
                    # should always find the worker
                    # j.shell()
                    continue

                job_running = w.current_job != 2147483647

                if job_running:
                    job = self.model_job.get(w.current_job)

                    if job != None and job.state != "OK" and j.data.time.epoch > job.time_start + job.timeout:
                        # WE ARE IN TIMEOUT
                        # print("TIMEOUT")
                        # print(w)
                        self._log_info("KILL:%s in worker %s" % (w.id, job.id))
                        gproc.terminate()
                        self.workers.pop(wid)
                        job.state = "ERROR"
                        job.error = "TIMEOUT"
                        job.time_stop = j.data.time.epoch
                        self.model_job.set(job)
                        print(job)
                        # make sure right nr of workers are active
                        self.worker_start()

            if test_workers_more():
                # test if we need to add workers
                while test_workers_more():
                    print("WORKERS START")
                    self.worker_start(subprocess=subprocess)
                gipc.gipc.gevent.joinall([p for p in self.workers.values()])
            else:

                # test if we have too many workers
                removed_one = False
                active_workers = [key for key in self.workers.keys()]
                active_workers.sort()
                for wid in active_workers:
                    gproc = self.workers[wid]
                    if gproc.exitcode != None:
                        raise j.exceptions.Base("subprocess should never have been exit-ed")
                    w = self.model_worker.get(wid)
                    if w == None:
                        continue

                    job_running = w.current_job != 2147483647
                    self._log_debug("job running:%s (%s)" % (w.id, job_running))

                    if w.halt == False and not job_running and self.queue_jobs_start.qsize() == 0:
                        if removed_one == False and test_workers_less():
                            self._log_debug("worker remove:%s" % wid)
                            removed_one = True
                            w.halt = True
                            self.model_worker.set(w)  # mark worker to halt
                            gproc.kill()
                            gproc.terminate()
                            self.model_worker.delete(wid)
                            gproc2 = self.workers[wid]
                            while gproc.is_alive():
                                gevent.sleep(0.1)
                                print("worker,killing:%s" % wid)
                            assert gproc2.is_alive() == False
                            self.workers.pop(wid)

            # print(self.workers)

            self._log_debug("nr workers:%s, queuesize:%s" % (self.workers_count, self.queue_jobs_start.qsize()))
            gevent.sleep(1)

    def schedule(
        self,
        method,
        *args,
        category="",
        timeout=0,
        inprocess=False,
        return_queues=[],
        return_queues_reset=False,
        gevent=False,
        **kwargs,
    ):
        """

        :param method:
        :param args:
        :param category:
        :param timeout:
        :param inprocess:
        :param return_queues: the result job id will be posted on the specified return_queue names (error or ok)
        :param return_queues_reset, if True will make sure the queues are empty
        :param gevent: means return queues will not be kept in redis, but in gevent queues
        :param kwargs:
        :return:
        """
        print("executing method {0} with *args {1} and **kwargs {2} ".format(method.__name__, args, kwargs))
        if inprocess:
            return method(*args, **kwargs)
        self.init()
        code = inspect.getsource(method)
        code = j.core.text.strip(code)
        code = code.replace("self,", "").replace("self ,", "").replace("self  ,", "")

        methodname = ""
        for line in code.split("\n"):
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ", "")

        if methodname == "":
            raise j.exceptions.Base("defname cannot be empty")

        key = j.data.hash.md5_string(code)
        new, action = self.action_get(key)
        if new:
            action.code = code
            action.key = key
            action.methodname = methodname
            self.model_action.set(action)

        job = self.model_job.new()
        job.action_id = action.id
        job.time_start = j.data.time.epoch
        job.state = "NEW"
        job.timeout = timeout
        job.category = category
        job.args = j.data.serializers.json.dumps(args)
        job.kwargs = j.data.serializers.json.dumps(kwargs)
        if not gevent:
            for qname in return_queues:
                job.return_queues.append(qname)
                if return_queues_reset:
                    q = j.clients.redis.queue_get(redisclient=j.clients.redis.core_get(), key="myjobs:%s" % qname)
                    q.reset()
        job = self.model_job.set(job)

        if gevent and return_queues != []:
            # self.return_queues[job.id]
            raise j.exceptions.Base("need to implement")

        self.queue_jobs_start.put(job.id)

        if job.id not in self.scheduled_ids:
            self.scheduled_ids.append(job.id)

        return job.id

    def halt(self, graceful=True, reset=True):

        if self.mainloop != None:
            self.mainloop.kill()

        if self.dataloop != None:
            self.dataloop.kill()

        for wid, gproc in self.workers.items():
            if gproc.exitcode != None:
                continue

            w = self.model_worker.get(wid)

            job_running = w.current_job != 2147483647

            if not graceful or not job_running:
                gproc.terminate()

        if reset:
            self.model_action.destroy()
            self.model_job.destroy()
            self.model_worker.destroy()
            # delete the queue
            while self.queue_jobs_start.get_nowait() != None:
                pass
            while self.queue_return.get_nowait() != None:
                pass

            self._init_ = False

    def reset(self):
        # kill leftovers from last time, if any
        self.halt(graceful=False, reset=True)
        assert self.queue_jobs_start.qsize() == 0
        assert self.queue_return.qsize() == 0

    def results(self, ids=None, timeout=100, die=True):
        """

        :param ids: if not specified then will be the last launched jobs
        :param timeout:
        :param die:  id die False then result will be the full objects
        :return:
        """

        if not ids:
            ids = self.scheduled_ids
        res = {}
        counter = 0
        now = time.time()
        if len(ids) > 0:
            current_id = ids[0]
        else:
            current_id = None

        while current_id:
            job = self.model_job.get(current_id)
            if job == None:
                raise j.exceptions.Base("job:%s not found" % current_id)
            if job.time_stop != 0:
                if job.state == "OK":
                    if die:
                        res[current_id] = job.result
                    else:
                        res[current_id] = job
                    if len(ids) > 0:
                        ids.pop(0)
                        if len(ids) > 0:
                            current_id = ids[0]
                        else:
                            current_id = None
                elif job.state == "ERROR":
                    logdict = job.error
                    j.core.tools.log2stdout(logdict)
                    if die:
                        self.scheduled_ids = []
                        raise RuntimeError("job:%s in error" % job.id)
                    else:
                        # we collect all errors so we need to make sure we get all other errors or non other errorobj
                        res[current_id] = job
                        if len(ids) > 0:
                            ids.pop(0)
                            if len(ids) > 0:
                                current_id = ids[0]
                            else:
                                current_id = None
                elif job.state == "HALTED":
                    # dont think we use at this point
                    j.shell()

            if len(ids) == 0:
                self.scheduled_ids = []
                return res

            counter += 1
            if time.time() - now > timeout:
                self.scheduled_ids = []
                raise j.exceptions.Base("timeout for results with jobids:%s" % ids)

            if not self.dataloop:
                # means we have to manually fetch the objects there is no dataloop doing it for us
                self._data_process_untill_empty(die=False)

        self.scheduled_ids = []
        return res

    workers_start = workers_start_tmux

    def wait(self, queue_name, size, timeout=120):
        queue = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % queue_name)
        with gevent.Timeout(timeout, False):
            while True:
                if queue.qsize() < size:
                    gevent.sleep(0)
                    continue
                return queue

    def test(self, name="basic", start=False):
        """
        it's run all tests
        kosmos 'j.servers.myjobs.test()'

        """
        if start:
            self.workers_start()

        self._test_run(name=name)

        self.halt(reset=True)

        print("TEST OK ALL PASSED")
