from Jumpscale import j
import copy
import tarfile
import time
from io import BytesIO

JSBASE = j.baseclasses.object


class Container(j.baseclasses.object):
    """Docker Container"""

    def __init__(self, obj, client):
        """
        Container object instance.

        @param obj str: obj of conainter as returned from the api.
        @param client obj(docker.Client()): client object from docker library.
        """

        self.client = client
        JSBASE.__init__(self)

        self.obj = obj
        self.name = obj["Names"][0][1::]  # remove the forward slash that docker adds to the name
        self.id = obj["Id"]

        self._ssh_port = None
        self._sshclient = None
        self._prefab = None
        self._executor = None

    @property
    def ssh_port(self):
        if self._ssh_port is None:
            self._ssh_port = self.public_port_get(22)
        return self._ssh_port

    @property
    def image(self):
        return self.info["Image"]

    @property
    def sshclient(self):
        if self._sshclient is None:
            sshclient = j.clients.ssh.new(
                addr=self.host, port=self.ssh_port, login="root", passwd="gig1234", timeout=10, allow_agent=True
            )
            self._sshclient = sshclient
        return self._sshclient

    @property
    def executor(self):
        if self._executor is None:
            self._executor = j.tools.executor.getLocalDocker(self.id)
        return self._executor

    @property
    def mounts(self):
        res = []
        mountinfo = self.info["Mounts"]
        for item in mountinfo:
            res.append((item["Source"], item["Destination"]))
        return res

    @property
    def status(self):
        return self.info["Status"]

    def prefab(self):
        if self._prefab is None:
            self._prefab = j.tools.prefab.get(self.executor, usecache=False)
        return self._prefab

    def run(self, cmd):
        """
        Run Docker exec with cmd.
        @param  cmd str: cmd to be executed will default run in bash
        """
        cmd2 = "docker exec -i -t %s %s" % (self.name, cmd)
        j.sal.process.executeWithoutPipe(cmd2)

    def execute(self, path):
        """
        execute file in docker
        """
        self.copy(path, path)
        self.run("chmod 770 %s;%s" % (path, path))

    @property
    def info(self):
        return self.obj

    def is_running(self):
        """
        Check conainter is running.
        """
        return self.info["State"] == "running"

    def ip_get(self):
        """
        Return ip of docker on hostmachine.
        """
        return self.info["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]

    def public_port_get(self, private_port):
        """
        Return public port that is forwarded to a port inside docker,
        this will only work if container has port forwarded the ports during
        run time.

        @param private_port int: private port number to look for its public port
        """

        if self.is_running() is False:
            raise j.exceptions.RuntimeError("docker %s is not running cannot get pub port." % self)

        if self.info["Ports"] is not None:
            for port in self.info["Ports"]:
                if port["PrivatePort"] == private_port:
                    return port["PublicPort"]

    def ssh_authorize(self, sshkeyname, password):
        home = j.builders.bash.home
        user_info = [j.builders.system.user.check(user) for user in j.builders.system.user.list()]
        users = [i["name"] for i in user_info if i["home"] == home]
        user = users[0] if users else "root"
        addr = self.info["Ports"][0]["IP"]
        port = self.info["Ports"][0]["PublicPort"]
        if not sshkeyname:
            sshkeyname = j.tools.configmanager.keyname
        instance = addr.replace(".", "-") + "-%s" % port + "-%s" % self.name

        sshclient = j.clients.ssh.new(instance=instance, addr=addr, port=port, login=user, passwd=password, timeout=300)
        sshclient.connect()
        sshclient.ssh_authorize(key=j.tools.configmanager.keyname, user="root")
        sshclient.config.delete()  # remove this temp sshconnection
        sshclient.close()

        # remove bad key from local known hosts file
        j.clients.sshkey.knownhosts_remove(addr)
        instance = addr.replace(".", "-") + "-%s" % port + "-%s" % self.name
        self._sshclient = j.clients.ssh.new(
            instance=instance,
            addr=addr,
            port=port,
            login="root",
            passwd="",
            keyname=j.tools.configmanager.keyname,
            allow_agent=True,
            timeout=300,
            addr_priv=addr,
        )

        j.tools.executor.reset()

    def destroy(self):
        """
        Stop and remove container.
        """
        # self.cleanAysfs()

        try:
            if self.is_running():
                self.stop()
            self.client.remove_container(self.id)
        except Exception as e:
            self._log_error("could not kill:%s" % self.id)
        finally:
            if self.id in j.sal.docker._containers:
                del j.sal.docker._containers[self.id]

    def start(self):
        """
        start instance of the container.
        """
        self.client.start(self.id)

    def stop(self):
        """
        Stop running instance of container.
        """
        self.client.stop(self.id)

    def restart(self):
        """
        Restart isntance of the container.
        """
        self.client.restart(self.id)

    def commit(self, imagename, msg="", delete=True, force=False, push=False, **kwargs):
        """
        imagename: name of the image to commit. e.g: jumpscale/myimage
        delete: bool, delete current image before doing commit
        force: bool, force delete
        """
        previous_timeout = self.client.timeout
        self.client.timeout = 3600

        if delete:
            res = j.sal.docker.client.images(imagename)
            if len(res) > 0:
                self.client.remove_image(imagename, force=force)
        self.client.commit(self.id, imagename, message=msg, **kwargs)

        self.client.timeout = previous_timeout

        if push:
            j.sal.docker.push(imagename)

    def __str__(self):
        return "docker:%s" % self.name

    __repr__ = __str__
