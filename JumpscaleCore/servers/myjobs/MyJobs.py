import inspect
from Jumpscale import j
import gipc
import gevent
import time
from .MyWorkerProcess import MyWorkerProcess

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

from .MyWorkerObject import MyWorkerObject


class MyJobs(j.baseclasses.testtools, j.baseclasses.object_config_collection):
    __jslocation__ = "j.servers.myjobs"
    _CHILDCLASS = MyWorkerObject

    def _init(self, **kwargs):
        self.queue_jobs_start = j.clients.redis.queue_get(redisclient=j.core.db, key="queue:jobs:start")
        self.queue_return = j.clients.redis.queue_get(redisclient=j.core.db, key="queue:jobs:return")

        self._workers_gipc = {}
        self._workers_gipc_nr_min = 1
        self._workers_gipc_nr_max = 10
        self._mainloop_gipc = None
        self._dataloop = None

        self.model_job = self._bcdb.model_get(schema=schema_job)
        self.model_action = self._bcdb.model_get(schema=schema_action)

        self.scheduled_ids = []

    def job_get(self, job_id):
        return self.model_job.get(job_id)

    def action_get(self, key, return_none_if_not_exist=False):

        res = self.model_action.find(key=key)
        if len(res) > 0:
            o = self.model_action.get(res[0].id)
            return False, o
        else:
            if return_none_if_not_exist:
                return
            o = self.model_action.new()
            return True, o

    def _bcdb_selector(self):
        return j.data.bcdb.get("myjobs", storclient=j.clients.rdb.client_get())

    @property
    def _workers_gipc_count(self):
        return len(self._workers_gipc.values())

    def worker_inprocess_start(self, nr=None, debug=False):
        """

        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        if not nr:
            nr = self._worker_next_get()
        w = self.get(name="w%s" % nr)
        w.type = "inprocess"
        w.debug = debug
        w.nr = nr
        w.start()

    def worker_tmux_start(self, nr=None, debug=False):
        """
        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        if not nr:
            nr = self._worker_next_get()
        w = self.get(name="w%s" % nr)
        w.type = "tmux"
        w.nr = nr
        w.debug = debug
        w.start()
        self._dataloop_start()

    def _worker_inprocess_start_from_tmux(self, nr):
        w = self.get(name="w%s" % nr)
        w.time_start = j.data.time.epoch
        w.last_update = j.data.time.epoch
        self._log_info("worker in process for tmux: %s" % nr)
        MyWorkerProcess(worker_id=w._id, onetime=False)

    def workers_tmux_start(self, nr_workers=4, debug=False):
        """

        run the workers in subprocess

        kosmos -p "j.servers.myjobs.workers_tmux_start()"
        kosmos -p "j.servers.myjobs.workers_tmux_start(nr_workers=4)"

        :return:
        """
        for i in range(nr_workers):
            self.worker_tmux_start(nr=i + 1, debug=debug)

    def worker_subprocess_start(self, nr=None, debug=False):
        """
        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        if not nr:
            nr = self._worker_next_get()
        w = self.get(name="w%s" % nr)
        w.type = "subprocess"
        w.debug = debug
        w.nr = nr
        w.start()
        self._dataloop_start()

    def _worker_next_get(self):
        last = 0
        for i in self._model.find():
            if i.nr > last:
                last = i.nr
        return last + 1

    def workers_subprocess_start(self, nr_fixed_workers=None, debug=False):
        """

        run the workers in subprocess

        kosmos -p "j.servers.myjobs.workers_subprocess_start()"
        kosmos -p "j.servers.myjobs.workers_subprocess_start(fixed_workers=10)"

        :return:
        """

        if not nr_fixed_workers:
            self._mainloop_gipc = gevent.spawn(self._main_loop_subprocess)
        else:
            for i in range(nr_fixed_workers):
                self.start_subprocess_worker(nr=i, debug=debug)

    def _dataloop_start(self):
        if not self._dataloop:
            self._dataloop = gevent.spawn(self._data_loop)

    def _dataloop_stop(self):
        if not self._dataloop:
            self._dataloop.kill()
            self._dataloop = None

    def workers_check(self, kill_workers_in_error=True):
        """
        kosmos "print(j.servers.myjobs.workers_check())"
        
        res,count,errors = j.servers.myjobs.workers_check()

        will check that workers are running

        :return:
        """

        # state* = "NEW,ERROR,BUSY,WAITING,HALTED" (E)

        def kill(worker_obj):
            if kill_workers_in_error:
                if worker_obj.pid > 0:
                    self._log_warning(
                        "will kill job, worker:%s pid:%s" % (worker_obj.id, worker_obj.pid), data=worker_obj
                    )
                    j.shell()
                    w
                else:
                    self._log_warning(
                        "cannot kill worker, workerid:%s pid:%s is unknown" % (worker_obj._id, worker_obj.pid),
                        data=worker_obj,
                    )

        count = 0
        errors = 0
        res = []
        for w in self.find():
            if w.state in ["NEW"] and w.last_update < j.data.time.epoch - 20:
                # means error should not be there
                w.state = "ERROR"
                w.error = "did not start queue to wait for work"
                w.save()
                errors += 1
                res.append(w)
                kill(w)
            elif w.state in ["WAITING"]:
                if w.last_update < j.data.time.epoch - 20:
                    # means error should not be there
                    w.state = "ERROR"
                    w.error = "queue started but watchdog failed, worker should have reported back"
                    kill(w)
                    w.save()
                    errors += 1
                else:
                    # means hapily waiting all ok
                    count += 1
                res.append(w)
            elif w.state in ["BUSY"]:
                if w.last_update < j.data.time.epoch - 7200:  # 2h
                    w.state = "ERROR"
                    w.error = "TIMEOUT, is waiting on work for longer than 2h"
                    w.save()
                    errors += 1
                    kill(w)
                else:
                    # job active but ok
                    count += 1
                res.append(w)
            elif w.state in ["ERROR"]:
                errors += 1
                res.append(w)
                kill(w)
            elif w.state in ["HALTED"]:
                pass
            else:
                raise j.exceptions.JSBUG("unknown state of worker")

        return res, count, errors

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
            data2 = j.data.serializers.json.loads(data)
            worker_object = self._model.get(objid)
            worker_object._data_update(data2)
            worker_object.save()
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

        # need to wait till first one comes
        r = self._data_process_1time(timeout=timeout, die=die)
        if not r:
            return

        while r is not None:
            if self.queue_return.empty:
                return
            r = self._data_process_1time(timeout=timeout, die=die)

    def _main_loop_subprocess(self):
        """
        gevent loop
        :return:
        """
        self._log_debug("monitor start")

        def test_workers_more():
            _workers_gipc_count = self._workers_gipc_count
            a = _workers_gipc_count < self._workers_gipc_nr_max
            b = _workers_gipc_count < self.queue_jobs_start.qsize() or _workers_gipc_count < self._workers_gipc_nr_min
            return a and b

        def test_workers_less():
            _workers_gipc_count = self._workers_gipc_count
            a = _workers_gipc_count > self._workers_gipc_nr_max
            b = _workers_gipc_count > self.queue_jobs_start.qsize() and _workers_gipc_count > self._workers_gipc_nr_min
            return a or b

        while True:

            self._log_debug("monitor run for subprocess loop")

            # #there is already 1 working, lets give 2 sec time before we start monitoring
            # gevent.sleep(2)

            # TEST for timeout
            wids = [key for key in self._workers_gipc.keys()]
            for wid in wids:
                if wid in self._workers_gipc:
                    gproc = self._workers_gipc[wid]
                else:
                    continue
                if gproc.exitcode != None:
                    raise j.exceptions.Base("subprocess should never have been exitted")
                w = self.get(wid)
                if w == None:
                    # should always find the worker
                    j.shell()
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
                        self._workers_gipc.pop(wid)
                        job.state = "ERROR"
                        job.error = "TIMEOUT"
                        job.time_stop = j.data.time.epoch
                        self.model_job.set(job)
                        print(job)
                        # make sure right nr of workers are active
                        self.worker_subprocess_start()

            if test_workers_more():
                # test if we need to add workers
                while test_workers_more():
                    print("WORKERS START")
                    self.worker_subprocess_start()
                gipc.gipc.gevent.joinall([p for p in self._workers_gipc.values()])
            else:

                # test if we have too many workers
                removed_one = False
                active_workers = [key for key in self._workers_gipc.keys()]
                active_workers.sort()
                for wid in active_workers:
                    gproc = self._workers_gipc[wid]
                    if gproc.exitcode != None:
                        raise j.exceptions.Base("subprocess should never have been exit-ed")
                    w = self.get(wid)
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
                            gproc2 = self._workers_gipc[wid]
                            while gproc.is_alive():
                                gevent.sleep(0.1)
                                print("worker,killing:%s" % wid)
                            assert gproc2.is_alive() == False
                            self._workers_gipc.pop(wid)
                            self.delete(wid)

            # print(self._workers_gipc)

            self._log_debug("nr workers:%s, queuesize:%s" % (self._workers_gipc_count, self.queue_jobs_start.qsize()))
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

    def stop(self, graceful=True, reset=True, timeout=60):

        if self._mainloop_gipc != None:
            self._mainloop_gipc.kill()

        if self._dataloop != None:
            self._dataloop.kill()

        for w in self.find():
            # look for the workers and ask for halt in nice way
            w.stop(hard=reset)

        timeout_end = j.data.time.epoch + timeout
        while not reset and graceful and j.data.time.epoch < timeout_end:
            active, count, errors = self.workers_check(True)
            if count == 0:
                break
            time.sleep(1)
            self._log_debug("wait gracefull shutdown")

        for wid, gproc in self._workers_gipc.items():
            if gproc.exitcode != None:
                continue

            w = self.get(wid)

            job_running = w.current_job != 2147483647

            if not graceful or not job_running:
                gproc.terminate()

        if reset:
            self.model_action.destroy()
            self.model_job.destroy()
            self._model.destroy()
            # delete the queue
            while self.queue_jobs_start.get_nowait() != None:
                pass
            while self.queue_return.get_nowait() != None:
                pass

            self._init_ = False

    def reset(self):
        # kill leftovers from last time, if any
        self.stop(graceful=False, reset=True)
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

            if not self._dataloop:
                # means we have to manually fetch the objects there is no dataloop doing it for us
                self._data_process_untill_empty(die=False)

        self.scheduled_ids = []
        return res

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
            self._workers_gipc_start()

        self._test_run(name=name)

        self.stop(reset=True)

        print("TEST OK ALL PASSED")
