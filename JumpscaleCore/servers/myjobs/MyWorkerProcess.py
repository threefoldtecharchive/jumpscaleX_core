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
    def _init(self, worker_id=None, onetime=False, showout=True, debug=False):
        """
        :return:
        """

        self.onetime = onetime
        self.showout = showout
        self.debug = debug

        assert worker_id

        if self.debug:
            j.application.debug = self.debug

        if not onetime:
            # make sure all traces of existing clients are gone
            j.data.bcdb._children = j.baseclasses.dict()
            j.application.subprocess_prepare()
            j.clients.redis._cache_clear()  # make sure we have redis connections empty, because comes from parent

        # MAKE SURE YOU DON'T REUSE SOCKETS FROM MOTHER PROCESSS
        j.core.db.source = "worker"  # this allows us to test
        self.redisclient = j.core.db
        self.bcdbclient = j.clients.redis.get(port=j.servers.myjobs.BCDB_CONNECTOR_PORT)

        self.queue_jobs_start = j.clients.redis.queue_get(
            redisclient=self.redisclient, key="queue:jobs:start", fromcache=False
        )
        # self.queue_return = j.clients.redis.queue_get(redisclient=redisclient, key="queue:jobs:return", fromcache=False)

        j.errorhandler.handlers.append(self.error_handler)

        storclient = j.clients.rdb.client_get(redisclient=self.redisclient)
        # important, test we're using the right redis client
        assert storclient._redis.source == "worker"

        self.bcdb = j.data.bcdb.get("myjobs", storclient=storclient)
        self.model_job = self.bcdb.model_get(schema=schemas.job)
        self.model_action = self.bcdb.model_get(schema=schemas.action)
        self.model_worker = self.bcdb.model_get(schema=schemas.worker)

        if not self.onetime:
            # if not onetime then will send all to queue which will be processed on parent process (the myjobs manager)
            # makes sure that we cannot start by coincidence the data processing loop
            # TODO: need to check this in the processing loop that this is not True
            j.servers.myjobs._i_am_worker = True
            self.model_job.nosave = True
            self.model_worker.nosave = True

        self.model_worker.trigger_add(self._worker_set)
        self.model_job.trigger_add(self._job_set)

        self.worker_obj = self._worker_get(worker_id)

        self.start()

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
        self.worker_obj.save()
        if not self.onetime:
            self._log_info("WORKER REMOVE SELF:%s" % self.id, data=self)
        else:
            self._log_info("WORKER ONETIME DONE")

    # DATA LOGIC
    def job_get(self, id):
        # call through redis client the local BCDB
        # get data as json
        # use model_schema to give the object
        return self._redis_get(id, self.model_job)

    def _redis_get(self, id, schema):
        key = f"{self.bcdb.name}:data:1:{schema._schema_url}"
        data = self.bcdbclient.hget(key, str(id))
        ddata = j.data.serializers.json.loads(data)
        return schema.new(ddata)

    def _redis_set(self, obj):
        key = f"{self.bcdb.name}:data:1:{obj._schema.url}"
        self.bcdbclient.hset(key, str(obj.id), obj._json)

    def _action_get(self, id):
        if self.onetime:
            return self.model_action.get(id, die=True)
        else:
            # call through redis client the local BCDB
            # get data as json
            # use model_schema
            return self._redis_get(id, self.model_action)

    def _worker_get(self, id):
        if self.onetime:
            return self.model_worker.get(id, die=True)
        else:
            return self._redis_get(id, self.model_worker)
            # call through redis client the local BCDB
            # get data as json
            # use model_schema
            # if exists put on self.worker_obj & return this one
            # if dont exists, quit

    def _worker_set(self, obj, action="save", propertyname=None, **kwargs):
        if action == "save":
            self._redis_set(obj)
            # call through redis client the local BCDB
            # get data as json (from _data) and use redis client to set to server

    def _job_set(self, obj, action="save", propertyname=None, **kwargs):
        if action == "save":
            # call through redis client the local BCDB
            # get data as json (from _data) and use redis client to set to server
            self._redis_set(obj)

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
        while True:
            res = None

            if self.onetime:
                while not res:
                    res = self.queue_jobs_start.get(timeout=0)
                    gevent.sleep(0.1)
                    self._log_debug("jobget from queue")
            else:
                res = self.queue_jobs_start.get(timeout=20)

            self.worker_obj = self._worker_get(self.id)
            if self.worker_obj.halt or res == b"halt":
                return self.stop()

            if res == None:
                if j.data.time.epoch > last_info_push + 20:
                    print(self.worker_obj)
                    self._log_info("queue request timeout, no data, continue", data=self.worker_obj)
                    self._state_set()
                    last_info_push = j.data.time.epoch
            else:
                self._log_debug("queue has data")
                jobid = int(res)
                job = self.job_get(jobid)
                self.job = job
                job.time_start = j.data.time.epoch
                skip = False
                relaunch = False
                for dep_id in job.dependencies:
                    job_deb = self.job_get(dep_id)
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
                        self._log_info("job queue empty, will wait 1 sec to relaunch the job", data=job)
                        time.sleep(1)
                    job.state = "NEW"
                    job.save()
                    self.queue_jobs_start.put(job.id)

                if not skip:
                    self.worker_obj.last_update = j.data.time.epoch
                    self.worker_obj.current_job = jobid

                    if job == None:
                        self._log_error("ERROR: job:%s not found" % jobid)
                        j.shell()
                    else:
                        # now have job
                        action = self._action_get(job.action_id)
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

                        if self.queue_jobs_start.qsize() == 0:
                            # make sure we already set here, otherwise no need because a new job is waiting anyhow
                            self._state_set()

            gevent.sleep(0)
            if self.onetime:
                self._state_set(state="HALTED")
                self.worker_obj.save()
                # need to make sure all gets processed
                return
