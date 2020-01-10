import sys
from Jumpscale import j
import gipc
import gevent
import time
import redis
from . import schemas
from .MyWorkerProcess import MyWorkerProcess
from .MyJobs import MyJobs
from .MyWorker import MyWorkers


class MyJobsFactory(j.baseclasses.factory_testtools):
    __jslocation__ = "j.servers.myjobs"
    _CHILDCLASSES = [MyWorkers, MyJobs]

    def _init(self, **kwargs):
        self.BCDB_CONNECTOR_PORT = 6380
        self.queue_jobs_start = j.clients.redis.queue_get(redisclient=j.core.db, key="queue:jobs:start")

        self._workers_gipc = {}
        self._workers_gipc_nr_min = 1
        self._workers_gipc_nr_max = 10
        self._mainloop_gipc = None
        self._mainloop_tmux = None
        self._mainloop_greenlet_redis = None

        self._init_models()

        self.scheduled_ids = []
        self._init_pre_schedule_ = False
        self._i_am_worker = False

    def _init_models(self):
        self._bcdb = self._bcdb_selector()
        if not j.threebot.active:
            j.servers.threebot.threebotserver_require()
        j.data.bcdb._master_set(j.threebot.active)
        self.model_action = j.clients.bcdbmodel.get(name="myjobs", schema=schemas.action)
        j.clients.bcdbmodel.get(name="myjobs", schema=schemas.worker)
        j.clients.bcdbmodel.get(name="myjobs", schema=schemas.job)

    def _init_pre_schedule(self, in3bot=False):
        if not self._init_pre_schedule_:

            assert self._i_am_worker is False
            # need to make sure at startup we process all data which is still waiting there for us
            assert self._children
            assert self.jobs
            assert self.workers
            # try:
            #     # start bcdb connector only if it's not started already
            #     j.clients.redis.get(port=self.BCDB_CONNECTOR_PORT).ping()
            # except (j.exceptions.Base, redis.ConnectionError):
            #     if in3bot:
            #         raise j.exceptions.Base("cannot connect to 3bot bcdb redis port")
            #     self._mainloop_greenlet_redis = gevent.spawn(
            #         self._bcdb.redis_server_start, port=self.BCDB_CONNECTOR_PORT
            #     )
            #     self._log_warning("waiting for redis interface of threebotserver to come up")
            #     self._bcdb.redis_server_wait_up(self.BCDB_CONNECTOR_PORT)
            self._init_pre_schedule_ = True

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
        return j.data.bcdb.get("myjobs")

    @property
    def _workers_gipc_count(self):
        return len(self._workers_gipc.values())

    def worker_inprocess_start(self, nr=1, debug=False, in3bot=False):
        """

        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        self._init_pre_schedule(in3bot=in3bot)
        if not nr:
            nr = self._worker_next_get()
        w = self.workers.get(name="w%s" % nr)
        w.type = "inprocess"
        w._state_set_new()
        w.debug = debug
        w.nr = nr
        w.start()

    def worker_tmux_start(self, nr=None, debug=False, startloop=True, in3bot=False):
        """
        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        self._init_pre_schedule(in3bot=in3bot)
        if not nr:
            nr = self._worker_next_get()
        w = self.workers.get(name="w%s" % nr)
        w.type = "tmux"
        w.nr = nr
        w.debug = debug
        if w.state in ["HALTED", "ERROR"]:
            w.state = "NEW"
        w.save()
        w.start()
        if not self._mainloop_tmux and startloop:
            self._mainloop_tmux = gevent.spawn(self._main_loop_tmux)

    def _worker_inprocess_start_from_tmux(self, nr):
        # make sure jobs schema loaded
        _ = self.jobs
        w = self.workers.get(name="w%s" % nr)
        w.time_start = j.data.time.epoch
        w.last_update = j.data.time.epoch
        w.state = "waiting"
        self._log_info("worker in process for tmux: %s" % nr)
        MyWorkerProcess(worker_id=w._id, onetime=False, showout=False)

    def workers_tmux_start(self, nr_workers=4, debug=False, in3bot=False):
        """

        run the workers in subprocess

        kosmos -p "j.servers.myjobs.workers_tmux_start()"
        kosmos -p "j.servers.myjobs.workers_tmux_start(nr_workers=4)"

        :return:
        """
        self._init_pre_schedule(in3bot=in3bot)
        for i in range(nr_workers):
            self.worker_tmux_start(nr=i + 1, debug=debug, startloop=False)
        if not self._mainloop_tmux:
            self._mainloop_tmux = gevent.spawn(self._main_loop_tmux)

    def worker_subprocess_start(self, nr=None, debug=False, in3bot=False):
        """
        :param nr: is the nr of the worker 1 to x will be a child with name w$nr e.g. w3
        :param debug:
        :return:
        """
        self._init_pre_schedule(in3bot=in3bot)
        if not nr:
            nr = self._worker_next_get()
        w = self.workers.get(name="w%s" % nr)
        w.type = "subprocess"
        w.debug = debug
        w.nr = nr
        w.start()

    def _worker_next_get(self):
        last = 0
        for i in self.workers._model.find():
            if i.nr > last:
                last = i.nr
        return last + 1

    def workers_subprocess_start(self, nr_fixed_workers=None, debug=False, in3bot=False):
        """

        run the workers in subprocess

        kosmos -p "j.servers.myjobs.workers_subprocess_start()"
        kosmos -p "j.servers.myjobs.workers_subprocess_start(fixed_workers=10)"

        :return:
        """
        self._init_pre_schedule(in3bot=in3bot)
        if not nr_fixed_workers:
            self._mainloop_gipc = gevent.spawn(self._main_loop_subprocess)
        else:
            for i in range(nr_fixed_workers + 1):
                self.worker_subprocess_start(nr=i, debug=debug)

    def workers_check(self, kill_workers_in_error=True):
        """
        kosmos "print(j.servers.myjobs.workers_check())"

        res,count,errors = j.servers.myjobs.workers_check()

        will check that workers are running

        :return:
        """

        def kill(worker_obj):
            if kill_workers_in_error:
                if worker_obj.pid > 0:
                    self._log_warning(
                        "will kill job, worker:%s pid:%s" % (worker_obj.id, worker_obj.pid), data=worker_obj
                    )
                else:
                    self._log_warning(
                        "cannot kill worker, workerid:%s pid:%s is unknown" % (worker_obj._id, worker_obj.pid),
                        data=worker_obj,
                    )

        count = 0
        errors = 0
        res = []
        for w in self.workers.find():
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

    def _main_loop_tmux(self, reset=False):
        """
        idea is to check how tmux is doing, if not enough workers add
        if stopped after certain period add again
        :param reset:
        :return:
        """
        timeout_error = 600
        timeout_busy = 1200
        while True:
            self._log_debug("check workers")
            for w in self.workers.find(reload=True):
                if w.state == "HALTED":
                    w.stop(hard=True)
                    if w.last_update < j.data.time.epoch - (timeout_error + 2):
                        w.delete()
                elif w.state in ["ERROR"]:
                    w._log_warning("WORKER IN ERROR:%s" % w.nr)
                    # auto restart when $timeout_error sec in error
                    if w.last_update < j.data.time.epoch - (timeout_error + 1):
                        w.stop(hard=True)
                        w.start()
                elif w.state in ["WAITING"]:
                    if w.last_update > j.data.time.epoch - timeout_error:
                        # w._log_info("no need to start worker:%s" % w.nr)
                        pass
                    else:
                        w._log_warning("worker was frozen because watchdog expired, will kill:%s" % w.nr)
                        w.stop(hard=True)
                        w.start()
                elif w.state in ["BUSY"]:
                    if reset:
                        w.stop(hard=True)
                        w.start()
                    if w.last_update < j.data.time.epoch - timeout_busy:
                        w._log_warning("worker was busy for %s min, will kill:%s" % (timeout_busy, w.nr))
                        w.stop(hard=True)
                        w.start()
                elif w.state in ["NEW"]:
                    w.start()

            time.sleep(10)

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
                w = self.workers.get(wid)
                if w is None:
                    # should always find the worker
                    j.shell()
                    continue

                job_running = w.current_job != 2147483647

                if job_running:
                    job = self.jobs.get(w.current_job)

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
                        self.jobs.set(job)
                        # print(job)
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
                    w = self.workers.get(wid, die=False)
                    if w is None:
                        # WHY IS THIS OK, SHOULD THIS NOT FAIL? TODO:
                        continue

                    job_running = w.current_job != 2147483647
                    self._log_debug("job running:%s (%s)" % (w.id, job_running))

                    if w.halt is False and not job_running and self.queue_jobs_start.qsize() == 0:
                        if removed_one is False and test_workers_less():
                            self._log_debug("worker remove:%s" % wid)
                            w.stop(True)
                            w.delete()

            # print(self._workers_gipc)

            self._log_debug("nr workers:%s, queuesize:%s" % (self._workers_gipc_count, self.queue_jobs_start.qsize()))
            gevent.sleep(1)

    def schedule(
        self,
        method,
        name=None,
        category="",
        timeout=0,
        dependencies=None,
        wait=False,
        die=True,
        args_replace=None,
        return_queues=None,
        return_queues_reset=None,
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
        self._init_pre_schedule()
        if not name:
            name = "j%s" % j.core.db.incr("myjobs.ourid")
        if self.jobs.exists(name=name):
            self.jobs.delete(name=name)
        if "self" in kwargs:
            kwargs.pop("self")
        job = self.jobs.new(
            name=name,
            method=method,
            dependencies=dependencies,
            args_replace=args_replace,
            return_queues=return_queues,
            return_queues_reset=return_queues_reset,
            kwargs=kwargs,
        )

        job.time_start = j.data.time.epoch
        job.state = "NEW"
        job.timeout = timeout
        job.category = category
        job.die = die
        self.scheduled_ids.append(job.id)
        self.queue_jobs_start.put(job.id)

        # never timeout
        if timeout == 0:
            timeout = None

        if wait:
            if not return_queues:
                return job.wait(die=die, timeout=timeout)
            return self.wait_queues(queue_names=return_queues, size=len([job.id]), die=die, timeout=timeout)

        assert job._data._autosave is True
        return job

    def stop(self, graceful=True, reset=True, timeout=60, hard=True):
        if self._mainloop_gipc != None:
            self._mainloop_gipc.kill()

        for w in self.workers.find(reload=True):
            # look for the workers and ask for halt in nice way
            w.stop(hard=hard)

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

            w = self.workers.get(id=wid)

            job_running = w.current_job != 2147483647

            if not graceful or not job_running:
                gproc.terminate()

        if self._mainloop_greenlet_redis:
            self._mainloop_greenlet_redis.kill()
        self._init_pre_schedule_ = False

        if reset:
            # delete the queue
            while self.queue_jobs_start.get_nowait() != None:
                pass
            self.reset_data()

            self._init_ = False

    def reset(self):
        # kill leftovers from last time, if any
        self.stop(graceful=False, reset=True)
        assert self.queue_jobs_start.qsize() == 0

    def reset_data(self):
        self.wait_queues_delete()
        self.model_action.reset()
        self.jobs.reset()
        self.workers.reset()
        self.scheduled_ids = []
        self.queue_jobs_start.reset()
        assert self.queue_jobs_start.qsize() == 0
        self._init()

    def check_all(self, die=True):
        for job in self.find(state="NEW"):
            job.check(die=die)
        for job in self.find(state="RUNNING"):
            job.check(die=die)

    def wait(self, ids=None, timeout=100, die=True):
        """

        :param ids: if not specified then will be the last launched jobs (see self scheduled_ids)
        :param timeout:
        :param die:  id die False then result will be the full objects
        :return: jobs
        """
        jobs = []
        if not ids:
            ids = j.servers.myjobs.scheduled_ids

        for obj in ids:
            if isinstance(obj, j.data.schema._JSXObjectClass):
                obj = self.jobs.get(id=obj.id)
                if obj not in jobs:
                    jobs.append(obj)
            elif isinstance(obj, j.baseclasses.object_config):
                obj.load()
                if obj not in jobs:
                    jobs.append(obj)
            elif isinstance(obj, int):
                obj = self.jobs.get(id=obj)
                obj.load()
                if obj not in jobs:
                    jobs.append(obj)
            else:
                raise j.exceptions.Input("can only be int or job object")

        if len(jobs) == 0:
            raise j.exceptions.BUG("jobs to wait on should not be None, there are no jobs in scheduled ids")

        with gevent.Timeout(timeout, False):
            for job in jobs:
                job.wait(die=die)
        return jobs

    def wait_queues(self, queue_names, size, timeout=120, die=True):
        if size == 0:
            return []

        queue = None
        queues = []
        res = []
        with gevent.Timeout(timeout, False):
            for queue_name in queue_names:
                queue = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:wait:%s" % queue_name)
                queues.append(queue)
                while queue.qsize() < size:
                    gevent.sleep(0)
            jobid = True
            while jobid:
                job = queue.get_nowait()
                if job:
                    job = j.data.serializers.json.loads(job.decode())
                    jobid = job["id"]
                    job = self.jobs.get(id=jobid)
                    if job.error and die:
                        # make sure all queues are reset
                        for queue in queues:
                            queue.reset()
                        raise j.exceptions.Base(f"job failed: {job.id}", data=self)
                    res.append(job)
                else:
                    jobid = False
            # make sure all queues are reset
            for queue in queues:
                queue.reset()
            return res

    def wait_queues_delete(self):
        for key in j.core.db.keys("myjobs:wait*"):
            j.core.db.delete(key)
            j.shell()

    def results(self, ids=None, return_queues=None, timeout=100, die=True):
        if ids is None:
            ids = self.scheduled_ids
        elif len(ids) == 0:
            return []
        if not return_queues:
            return [job.result for job in self.wait(ids=ids, timeout=timeout, die=die)]
        else:
            return [
                job.result
                for job in self.wait_queues(queue_names=return_queues, size=len(ids), timeout=timeout, die=die)
            ]

    def wait_queue(self, queue_name, size=1, timeout=120, die=True):
        res = self.wait_queues(queue_names=[queue_name], size=size, timeout=timeout, die=die)
        if res:
            return res[0]

    def _test_teardown(self):
        j.servers.myjobs.stop(timeout=10, reset=False, graceful=False)
        try:
            redis = j.servers.startupcmd.get("redis_6380")
            redis.stop()
            redis.wait_stopped()
        except:
            j.sal.process.killProcessByPort(6380)

        j.servers.myjobs.workers.reset()

    def _test_setup(self):
        # make sure client for myjobs properly configured

        j.core.db.redisconfig_name = "core"
        storclient = j.clients.rdb.client_get(bcdbname="myjobs")
        myjobs_bcdb = j.data.bcdb.get("myjobs", storclient=storclient)
        bcdb = j.data.bcdb.system
        adminsecret_ = j.data.hash.md5_string(j.core.myenv.adminsecret)
        redis_server = j.data.bcdb.redis_server_get(port=6380, secret=adminsecret_)
        # just to make sure we don't have it open to external

        j.servers.myjobs.model_action.model.index_rebuild()
        j.servers.myjobs.workers._model.index_rebuild()
        j.servers.myjobs.jobs._model.index_rebuild()

        cmd = """
                . {DIR_BASE}/env.sh;
                kosmos 'j.data.bcdb.get("myjobs").redis_server_start(port=6380)'
                """

        self._cmd = j.servers.startupcmd.get(name="redis_6380", cmd_start=cmd, ports=[6380], executor="tmux")
        self._cmd.start()
        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeout=15)

    def test(self, name="", **kwargs):
        """
        it's run all tests
        kosmos 'j.servers.myjobs.test()'

        """

        try:
            self._test_run(name=name, **kwargs)
        except:
            self._test_teardown()
            raise
        print("TEST OK ALL PASSED")
