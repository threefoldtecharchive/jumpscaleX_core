from Jumpscale import j

import pudb
import sys
import gevent
import signal
import os


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
            j.core.myenv.debug = self.debug

        # make sure all traces of existing clients are gone
        j.application.subprocess_prepare()
        j.data.bcdb._children = j.baseclasses.dict()

        j.clients.redis._cache_clear()  # make sure we have redis connections empty, because comes from parent

        # MAKE SURE YOU DON'T REUSE SOCKETS FROM MOTHER PROCESSS
        j.core.db.source = "worker"  # this allows us to test
        redisclient = j.core.db

        self.queue_jobs_start = j.clients.redis.queue_get(
            redisclient=redisclient, key="queue:jobs:start", fromcache=False
        )
        self.queue_return = j.clients.redis.queue_get(redisclient=redisclient, key="queue:jobs:return", fromcache=False)

        # test we are using the right redis client
        assert self.queue_jobs_start._db_.source == "worker"
        assert self.queue_return._db_.source == "worker"

        j.errorhandler.handlers.append(self.error_handler)

        storclient = j.clients.rdb.client_get(redisclient=redisclient)
        # important, test we're using the right redis client
        assert storclient._redis.source == "worker"

        self.bcdb = j.data.bcdb.get("myjobs", storclient=storclient)
        self.model_job = self.bcdb.model_get(url="jumpscale.myjobs.job")
        self.model_action = self.bcdb.model_get(url="jumpscale.myjobs.action")
        self.model_worker = self.bcdb.model_get(url="jumpscale.myjobs.worker")

        self.model_job.nosave = True
        self.model_action.nosave = True
        self.model_worker.nosave = True

        self.model_worker.trigger_add(self._save_data)
        self.model_job.trigger_add(self._save_job)

        self.data = self._worker_get(worker_id)
        self.data.state = "new"
        self.data.current_job = 2147483647  # means nil
        self.data.id = worker_id
        self.data.pid = os.getpid()
        self.data.save()  # save in bcdb will not happen because readonly is True, it will trigger the triggers

        self.start()

    def return_data(self, cat, obj):
        # self._log("return data", data=obj)
        data = [cat, obj.id, obj._json]
        data = j.data.serializers.json.dumps(data)
        self.queue_return.put(data)

    def error_handler(self, logdict):
        data = j.data.serializers.json.dumps(logdict)
        data2 = ["E", None, data]
        data3 = j.data.serializers.json.dumps(data2)
        self.queue_return.put(data3)

    def _save_data(self, obj, action, propertyname, **kwargs):
        if action == "save":
            self.return_data("W", obj)

    def _save_job(self, obj, action, propertyname, **kwargs):
        if action == "save":
            self.return_data("J", obj)

    def stop(self):
        self.data.state = "halted"
        self.data.current_job = 2147483647
        self.data.last_update = j.data.time.epoch
        self.data.halt = False
        self.data.pid = 0
        self.data.save()
        self._log_info("WORKER REMOVE SELF:%s" % self.data.id)

    def _job_get(self, id):
        deadline = j.data.time.epoch + 3
        while deadline > j.data.time.epoch:
            res = self.model_job.get(id, die=False)
            if res:
                return res
        j.shell()
        raise j.exceptions.JSBUG("job should always be there:%s" % id)

    def _action_get(self, id):
        deadline = j.data.time.epoch + 3
        while deadline > j.data.time.epoch:
            res = self.model_action.get(id, die=False)
            if res:
                return res
        raise j.exceptions.JSBUG("action should always be there:%s" % id)

    def _worker_get(self, id):
        deadline = j.data.time.epoch + 3
        while deadline > j.data.time.epoch:
            res = self.model_worker.get(id, die=False)
            if res:
                return res
        self._log_info("worker object no longer exists, so I need to stop, prob reset of data")
        sys.exit(0)

    def start(self):
        self._log_info("start", data=self.data)
        # initial waiting state
        self.data.last_update = j.data.time.epoch
        self.data.current_job = 2147483647
        self.data.state = "waiting"
        self.data.save()
        last_info_push = j.data.time.epoch
        while True:
            res = None

            if self.onetime:
                while not res:
                    res = self.queue_jobs_start.get(timeout=0)
                    gevent.sleep(0.1)
                    self._log_debug("jobget")
            else:
                res = self.queue_jobs_start.get(timeout=1)

            self.data = self._worker_get(self.data.id)
            if self.data.halt or res == b"halt":
                return self.stop()

            if res == None:
                self._log_info("queue request timeout, no data, continue", data=self.data)
                if j.data.time.epoch > last_info_push + 20:
                    self.data.last_update = j.data.time.epoch
                    self.data.current_job = 2147483647
                    self.data.state = "waiting"
                    self.data.save()
                    last_info_push = j.data.time.epoch
            else:
                self._log_debug("queue has data")
                jobid = int(res)
                job = self._job_get(jobid)
                skip = False
                relaunch = False
                jobdata = job._ddict
                for dep_id in job.dependencies:
                    job_deb = self._job_get(dep_id)
                    if job_deb.state in ["ERROR", "HALTED"]:
                        job.state = job_deb.state
                        job.result = "cannot run because dependency failed: %s" % job_deb.id
                        job.error["dependency_failure"] = job_deb.id
                        job.time_stop = j.data.time.epoch
                        job.save()
                        skip = True
                    elif job_deb.state not in ["OK"]:
                        skip = True
                        # put the job back at end of queue, it needs to be done could not do yet
                        if job_deb.state in ["NEW"]:
                            relaunch = True

                if skip and relaunch:
                    self.queue_jobs_start.put(job.id)

                if not skip:
                    self.data.last_update = j.data.time.epoch
                    self.data.current_job = jobid

                    if job == None:
                        self._log_error("ERROR: job:%s not found" % jobid)
                        j.shell()
                        w
                    else:
                        # now have job
                        action = self._action_get(job.action_id)
                        kwargs = job.kwargs
                        args = job.args

                        self.data.last_update = j.data.time.epoch
                        self.data.current_job = jobid  # set current jobid
                        self.data.state = "busy"
                        self.data.save()

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
                                res = deadline(job.timeout)(method)(*args, job=job, **kwargs)
                            else:
                                res = deadline(job.timeout)(method)(*args, **kwargs)
                        except BaseException as e:
                            tb = sys.exc_info()[-1]
                            if isinstance(e, gevent.Timeout):
                                msg = "time out"
                                e = j.exceptions.Base(msg)
                            else:
                                msg = "cannot execute action"
                                job.time_stop = j.data.time.epoch
                            logdict = j.core.tools.log(
                                tb=tb, exception=e, msg=msg, data=action.code, stdout=self.showout
                            )
                            job.error = logdict
                            job.state = "ERROR"

                            job.save()

                            if self.debug:
                                pudb.post_mortem(tb)

                            if self.onetime:
                                return
                            continue

                        try:
                            job.result = j.data.serializers.json.dumps(res)
                        except Exception as e:
                            job.error = (
                                str(e)
                                + "\nCOULD NOT SERIALIZE RESULT OF THE METHOD, make sure json can be used on result"
                            )
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

                        self.data.state = "waiting"
                        self.data.current_job = 2147483647
                        self.data.last_update = j.data.time.epoch
                        self.data.save()

            gevent.sleep(0)
            if self.onetime:
                self.data.state = "halted"
                self.data.save()
                return
