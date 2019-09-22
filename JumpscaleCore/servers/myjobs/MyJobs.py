from Jumpscale import j
from . import schemas
import inspect
import gevent


class MyJob(j.baseclasses.object_config):

    _name = "job"
    _SCHEMATEXT = schemas.job

    def _init(self, method=None, dependencies=None, args_replace=None, **kwargs2):

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

        if method:
            self.process_code(method, args_replace)

    def _children_get(self, filter=None):
        """
        :param filter: is '' then will show all, if None will ignore _
                when * at end it will be considered a prefix
                when * at start it will be considered a end of line filter (endswith)
                when R as first char its considered to be a regex
                everything else is a full match
        :return:
        """
        x = []
        for key, item in self._children.items():
            x.append(item)
        if len(x) > 49:
            return x
        for item in self.find(state="OK"):
            if item not in x:
                x.append(item)
        for item in self.find(state="NEW"):
            if item not in x:
                x.append(item)
        for item in self.find(state="ERROR"):
            if item not in x:
                x.append(item)
        for item in self.find(state="RUNNING"):
            if item not in x:
                x.append(item)
        return self._filter(filter=filter, llist=x, nameonly=False)

    def process_code(self, method, args_replace):
        code = inspect.getsource(method)
        code = j.core.text.strip(code)
        code = code.replace("self,", "").replace("self ,", "").replace("self  ,", "")

        if args_replace:
            code = j.core.tools.text_replace(code, text_strip=False, args=args_replace)

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
        if self.state == "ERROR":
            if self.error_cat == "NA":
                self.error_cat = "ERROR"
            self.save()
            if self.error:
                j.core.tools.log2stdout(self.error)
            if die:
                raise j.exceptions.Base(f"job failed: {self.id}", data=self)
            return True
        if self.time_stop == 0:
            if self.timeout and self.time_start + self.timeout < j.data.time.epoch:
                # means we have timeout
                self.error_cat = "TIMEOUT"
                self.save()
                if die:
                    raise j.exceptions.Timeout(f"Job timed out: {self.id}")
            else:
                # nothing wrong found, can return
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
        event = j.servers.myjobs.events.get(self.id, None)
        ready = self.check_ready(die=die, load=False)
        if ready:
            return True
        if event:
            event.wait(timeout)
            ready = self.check_ready(die=die, load=True)
            if ready:
                return True

        with gevent.Timeout(timeout, False):
            while True:
                if self.check_ready(die=die):
                    return True
                gevent.sleep(0.2)


class MyJobs(j.baseclasses.object_config_collection):

    _CHILDCLASS = MyJob
    _name = "jobs"
