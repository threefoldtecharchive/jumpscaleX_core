from Jumpscale import j
from . import schemas

import pudb
import sys
import gevent
import os
import time


def deadline(timeout, *args):
    def decorate(f):
        def new_f(*args, **kwargs):
            if timeout:
                with gevent.Timeout(timeout):
                    return f(*args, **kwargs)
            return f(*args, **kwargs)

        new_f.__name__ = f.__name__
        return new_f

    return decorate


class MyWorkerProcess(j.baseclasses.object):
    def _init(self, worker_id=None, onetime=False, showout=False, debug=False):
        """
        :return:
        """

        self.onetime = onetime
        self.showout = showout
        self.debug = debug

        j.servers.threebot.threebotserver_require()

        assert worker_id

        if self.debug:
            j.application.debug = self.debug

        if not onetime:
            # make sure all traces of existing clients are gone
            j.data.bcdb._instances = j.baseclasses.dict()
            j.application.subprocess_prepare()
            j.clients.redis._cache_clear()  # make sure we have redis connections empty, because comes from parent

        self.redisclient = j.core.db

        if not self.debug:
            self.queue_jobs_start = j.clients.redis.queue_get(
                redisclient=self.redisclient, key="queue:jobs:start", fromcache=False
            )
        else:
            self.queue_jobs_start = j.clients.redis.queue_get(
                redisclient=self.redisclient, key="queue:debug_jobs:start", fromcache=False
            )

        j.errorhandler.handlers.append(self.error_handler)

        found = j.data.bcdb.exists("myjobs")
        while not found:
            found = j.data.bcdb.exists("myjobs")
            time.sleep(0.1)

        self.bcdb = j.data.bcdb.get("myjobs")

        self.model_job = j.clients.bcdbmodel.get(name=self.bcdb.name, schema=schemas.job)
        self.model_action = j.clients.bcdbmodel.get(name=self.bcdb.name, schema=schemas.action)
        self.model_worker = j.clients.bcdbmodel.get(name=self.bcdb.name, schema=schemas.worker)

        self.model_job.trigger_add(self._obj_print)
        self.model_action.trigger_add(self._obj_print)
        self.model_worker.trigger_add(self._obj_print)

        if not self.onetime:
            # if not onetime then will send all to queue which will be processed on parent process (the myjobs manager)
            # makes sure that we cannot start by coincidence the data processing loop
            # TODO: need to check this in the processing loop that this is not True
            j.servers.myjobs._i_am_worker = True

        self.worker_obj = self.model_worker.get(worker_id)

        self.start()

    def _obj_print(self, model, obj, kosmosinstance=None, action=None, propertyname=None):
        self._log_debug("action: %s" % action, data=obj)

    @property
    def id(self):
        return self.worker_obj.id

    def error_handler(self, logdict):
        # TODO: use actor error_handler on the redis server, ask Kristof what we will do
        pass

    def stop(self):
        self.worker_obj.state = "halted"
        self.worker_obj.current_job = 2147483647
        self.worker_obj.last_update = j.data.time.epoch
        self.worker_obj.halt = False
        self.worker_obj.pid = 0
        self._redis_set(self.worker_obj)
        self.worker_obj.save()
        if not self.onetime:
            self._log_info("WORKER REMOVE SELF:%s" % self.id, data=self)
        else:
            self._log_info("WORKER ONETIME DONE")

    ################

    def _state_set(self, state="WAITING"):
        self.worker_obj.state = state
        self.worker_obj.current_job = 2147483647
        self.worker_obj.last_update = j.data.time.epoch
        self.worker_obj.save()

    def start(self):
        self._log_info("start", data=self.worker_obj)
        # initial waiting state
        self.worker_obj.last_update = j.data.time.epoch
        self.worker_obj.current_job = 2147483647
        self.worker_obj.state = "WAITING"
        self.worker_obj.pid = os.getpid()
        self.worker_obj.save()
        last_info_push = j.data.time.epoch

        def queue_results(job):
            """
            add job results to queues, if there
            :param job: job obj
            """
            for queue_name in job.return_queues:
                queue = j.clients.redis.queue_get(redisclient=j.core.db, key="myjobs:%s" % queue_name)
                data = {"id": job.id, "result": job.result, "state": job.state._string}
                queue.put(j.data.serializers.json.dumps(data))

        while True:
            res = None

            if self.onetime:
                while not res:
                    res = self.queue_jobs_start.get(timeout=0)
                    gevent.sleep(0.1)
                    self._log_debug("jobget from queue")
            else:
                res = self.queue_jobs_start.get(timeout=20)

            self.worker_obj = self.model_worker.get(self.id)
            if self.worker_obj.halt or res == b"halt":
                return self.stop()

            if res is None:
                if j.data.time.epoch > last_info_push + 20:
                    # print(self.worker_obj)
                    # self._log_info("queue request timeout, no data, continue", data=self.worker_obj)
                    self._state_set()
                    last_info_push = j.data.time.epoch
            else:
                # self._log_debug("queue has data")
                jobid = int(res)
                try:
                    job = self.model_job.get(jobid)
                except Exception as e:
                    if not self.model_job.exists(jobid):
                        self._log_warning("job with:%s did not exist" % jobid)
                        continue
                    raise

                self.job = job
                job.time_start = j.data.time.epoch
                skip = False
                relaunch = False
                for dep_id in job.dependencies:
                    job_deb = self.model_job.get(dep_id)
                    if job_deb.state in ["ERROR"]:
                        job.state = job_deb.state

                        msg = f"cannot run because dependency failed: {job_deb.id}"
                        job.result = msg
                        log = j.core.tools.log(msg, stdout=False)
                        log["dependency_failure"] = job_deb.id
                        job.error = log
                        job.time_stop = j.data.time.epoch
                        job.save()
                        skip = True
                    elif job_deb.state not in ["OK", "DONE"]:
                        skip = True
                        # put the job back at end of queue, it needs to be done could not do yet
                        relaunch = True

                if skip and relaunch:
                    if self.queue_jobs_start.qsize() == 0:
                        # means we are waiting for some jobs to finish, lets wait 1 sec before we throw this job back on queue
                        # self._log_info("job queue empty, will wait 1 sec to relaunch the job", data=job)
                        time.sleep(1)
                    job.state = "NEW"
                    job.save()
                    self.queue_jobs_start.put(job.id)

                if not skip:
                    self.worker_obj.last_update = j.data.time.epoch
                    self.worker_obj.current_job = jobid

                    if job is None:
                        self._log_error("ERROR: job:%s not found" % jobid)
                        j.shell()
                    else:
                        # now have job
                        action = self.model_action.get(job.action_id)
                        kwargs = job.kwargs

                        self.worker_obj.last_update = j.data.time.epoch
                        self.worker_obj.current_job = jobid  # set current jobid
                        self.worker_obj.state = "busy"
                        self.worker_obj.save()

                        if self.showout:
                            self._log_info("execute", data=job)

                        try:
                            exec(action.code)
                            # better not to use eval but the JSX coderunner?
                            method = eval(action.methodname)
                        except Exception as e:
                            tb = sys.exc_info()[-1]
                            logdict = j.core.tools.log(
                                tb=tb, exception=e, msg="cannot compile action", data=action.code, stdout=self.showout
                            )

                            job.error = logdict
                            job.state = "ERROR"
                            job.time_stop = j.data.time.epoch
                            job.save()

                            queue_results(job)

                            if self.debug:
                                pudb.post_mortem(tb)

                            if self.onetime:
                                return
                            continue

                        try:
                            if job.dependencies != []:
                                res = deadline(job.timeout)(method)(process=self, **kwargs)
                            else:
                                res = deadline(job.timeout)(method)(**kwargs)
                        except BaseException as e:
                            tb = sys.exc_info()[-1]
                            if isinstance(e, gevent.Timeout):
                                msg = "time out"
                                e = j.exceptions.Base(msg)
                                job.error_cat = "TIMEOUT"
                            else:
                                msg = "cannot execute action"
                            logdict = j.core.tools.log(
                                tb=tb, exception=e, msg=msg, data=action.code, stdout=self.showout
                            )
                            job.state = "ERROR"
                            job.time_stop = j.data.time.epoch
                            job.error = logdict
                            job.save()

                            queue_results(job)

                            if self.debug:
                                pudb.post_mortem(tb)

                            if self.onetime:
                                return
                            continue

                        try:
                            job.result = j.data.serializers.json.dumps(res)
                        except Exception as e:
                            e.message_pub = "could not json serialize result of job"
                            try:
                                job.error = e.logdict
                            except Exception as e:
                                job.error = str(e)
                            job.state = "ERROR"
                            job.time_stop = j.data.time.epoch
                            job.save()
                            queue_results(job)
                            if self.showout:
                                self._log_error("ERROR:%s" % e, exception=e, data=job)
                            if self.onetime:
                                return
                            continue

                        job.time_stop = j.data.time.epoch
                        job.state = "OK"

                        if self.showout:
                            self._log("OK", data=job)

                        job.save()
                        queue_results(job)
                        if self.queue_jobs_start.qsize() == 0:
                            # make sure we already set here, otherwise no need because a new job is waiting anyhow
                            self._state_set()

            gevent.sleep(0)
            if self.onetime:
                self._state_set(state="HALTED")
                self.worker_obj.save()
                # need to make sure all gets processed
                return
