from Jumpscale import j
import inspect
import gevent


class MyJob(j.baseclasses.object_config):

    _name = "job"

    _SCHEMATEXT = """
        @url = jumpscale.myjobs.job
        name* = ""
        category*= ""
        time_start = 0 (T)
        time_stop = 0 (T)
        state* = "NEW,ERROR,OK,RUNNING" (E)
        error_cat = "NA,TIMEOUT,CRASH,HALTED"  (E)
        timeout = 0
        action_id* = 0
        kwargs = (dict)
        result_json = "" (S)
        error = (dict)
        return_queues = (LS)
        die = false (B)
        #will not execute this one before others done
        dependencies = (LI)
        
        """

    def _init(
        self, method=None, dependencies=None, args_replace=None, return_queues_reset=None, return_queues=None, **kwargs2
    ):

        # leave this check for now please
        assert self._bcdb.storclient._check_cat == "myjobs"

        if dependencies:
            for dep in dependencies:
                if isinstance(dep, j.data.schema._JSXObjectClass):
                    self.dependencies.append(dep.id)
                elif isinstance(dep, int):
                    self.dependencies.append(dep)
                else:
                    raise j.exceptions.Input("only jsx obj (job) or int supported in dependencies")

        if args_replace:
            for key, val in args_replace.items():
                self.kwargs[key] = val

        if return_queues:
            for qname in return_queues:
                self.return_queues.append(qname)
                if return_queues_reset:
                    q = j.clients.redis.queue_get(redisclient=j.clients.redis.core_get(), key="myjobs:%s" % qname)
                    q.reset()

        if method:
            self.process_code(method)

    @property
    def result(self):
        return j.data.serializers.json.loads(self.result_json)

    # @result.setter
    # def result(self, v):
    #     j.shell()
    #     self.result_json = j.data.serializers.json.dumps(v)

    def process_code(self, method):
        code = inspect.getsource(method)
        code = j.core.text.strip(code)
        code = code.replace("self,", "").replace("self ,", "").replace("self  ,", "")

        code = j.core.tools.text_replace(code, text_strip=False, args=self.kwargs)

        methodname = ""
        for line in code.split("\n"):
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ", "")

        if methodname == "":
            raise j.exceptions.Base("defname cannot be empty")

        key = j.data.hash.md5_string(code)
        new, action = j.servers.myjobs.action_get(key)
        if new:
            action.code = code
            action.key = key
            action.methodname = methodname
            j.servers.myjobs.model_action.set(action)

        self.action_id = action.id

        # if gevent and return_queues != []:
        #     # self.return_queues[self.id]
        #     raise j.exceptions.Base("need to implement")

        self.save()

    def check_ready(self, die=True, load=True):
        """
        checks if there is a timeout or an error an error will be raised unless if die==False
        it will make sure that the object data is right e.g. state, time, ...

        will return False if job is finished (error or not)
        if True nothing to do

        :return:
        """
        if load:
            self.load()
        if self.time_stop == 0:
            # if time stop filled in then the job does not need any further processing
            if self.state == "ERROR":
                self.time_stop = j.data.time.epoch
                if self.error_cat == "NA":
                    self.error_cat = "ERROR"

            elif self.time_start + self.timeout > j.data.time.epoch:
                self.time_stop = j.data.time.epoch
                escalate = True
                # means we have timeout
                self.error_cat = "TIMEOUT"
                self.save()
            else:
                # nothing wrong found, can return
                return False

            self.save()
            logdict = job.error
            j.core.tools.log2stdout(logdict)
            if die:
                raise j.exceptions.BASE("job failed:%s" % self.id, data=self)
            return False
        return True

    @property
    def running(self):
        return self.check_ready()

    def start(self):
        self._log_debug("executing method {0} with **kwargs {1} ".format(self.name, self.kwargs))
        j.servers.myjobs.scheduled_ids.append(self.id)
        j.servers.myjobs.queue_jobs_start.put(self.id)

    def kill(self):
        """
        check which worker is executing and then kill the worker
        :return:
        """
        j.shell()
        self.check_ready()

    def wait(self, timeout=None, die=True):
        with gevent.Timeout(timeout, False):
            while True:
                if self.check_ready(die=die):
                    return True
                gevent.sleep(0.2)


class MyJobs(j.baseclasses.object_config_collection):

    _CHILDCLASS = MyJob
    _name = "jobs"
