import os
import shutil
import json
import inspect
import re
import time
from typing import Dict
from ExecutorSSH import ExecutorSSH
from WireGuardServer import WireGuardServer
from .DockerConfig import DockerConfig


class DockerContainer:
    def __init__(self, myenv, name="default", image=None, startupcmd=None, ports=None, identity=None):
        """
        if you want to start from scratch use: "phusion/baseimage:master"

        if codedir not specified will use {DIR_BASE}/code
        """
        self._my = myenv
        self._tools = myenv.tools

        if name == "shared":
            raise self._tools.exceptions.JSBUG("should never be the shared obj")
        if not self._my.docker._init:
            raise self._tools.exceptions.JSBUG("make sure to call self._my.docker.init() bedore getting a container")
        self._my.docker._dockers[name] = self

        self.config = DockerConfig(myenv, name=name, image=image, startupcmd=startupcmd, ports=ports)

        if self.config.portrange is None:
            self.config._find_port_range()
            self.config.save()

        self._my.sshagent.key_default_name

        self._wireguard = None
        self._executor = None

    def done_get(self, name):
        name = name.strip().lower()
        path = "/root/state/%s" % name
        try:
            self.dexec("cat %s" % path)
        except:
            return False
        return True

    def done_set(self, name):
        name = name.strip().lower()
        path = "/root/state/%s" % name
        self.dexec("touch %s" % path)

    def done_reset(self, name=None):
        if not name:
            self.dexec("rm -rf /root/state")
            self.dexec("mkdir -p /root/state")
        else:
            name = name.strip().lower()
            path = "/root/state/%s" % name
            self.dexec("rm -f %s" % path)

    @property
    def executor(self):
        if not self._executor:
            self._executor = ExecutorSSH(
                self._my, addr=self.config.ipaddr, port=self.config.sshport, debug=False, name=self.config.name
            )
        return self._executor

    @property
    def container_exists_config(self):
        """
        returns True if the container is defined on the filesystem with the config file
        :return:
        """
        if self._tools.exists(self._path):
            return True

    @property
    def mount_code_exists(self):
        m = self.info["Mounts"]
        for item in m:
            if item["Destination"] == "/sandbox/code":
                return True
        return False

    @property
    def container_exists_in_docker(self):
        return self.name in self._my.docker.containers_names()

    @property
    def container_running(self):
        return self.name in self._my.docker.containers_running()

    @property
    def _path(self):
        return self.config.path_vardir

    @property
    def image(self):
        return self.config.image

    @image.setter
    def image(self, val):
        val = self._image_clean(val)
        if self.config.image != val:
            self.config.image = val
            self.config.save()

    def _image_clean(self, image=None):
        if image == None:
            return self.config.image
        if ":" in image:
            image = image.split(":")[0]
        return image

    @property
    def name(self):
        return self.config.name

    def install(self, update=True, stop=False, delete=False):
        return self.start(update=update, stop=stop, delete=delete, mount=True)

    def start(self, stop=False, delete=False, update=False, ssh=None, mount=None, pull=False, image=None, portmap=True):
        """
        @param mount : will mount the code dir from the host or not, default True
            True means: will force the mount
            None means: don't check mounted or not
            False means: will make sure is not mounted
        @param stop: stop the container if it was started
        @param delete: delete the container if it was there
        @param update: update ubuntu and some required base modules
        @param ssh: make sure ssh has been configured so you can access if from local
            True means: use ssh & configure
            None means: don't impact sshconfig, just leave as it is right now, don't do anything
            False means: remove ssh config if there is one

        @param image: can overrule the specified image at config time, normally leave empty

        @param portmap: if you want to map ports from host to docker container

        """
        if not image:
            image = self.image
        if not self.container_exists_config:
            raise self._tools.exceptions.Operations("ERROR: cannot find docker with name:%s, cannot start" % self.name)

        if pull:
            # lets make sure we have the latest image, ONLY DO WHEN FORCED, NOT STD
            self._tools.execute(f"docker image pull {image}", interactive=True)
            stop = True  # means we need to stop now, because otherwise we can't know we start from right image

        if delete:
            self.delete()
        else:
            if stop:
                self.stop()

        if self.isrunning():
            if mount == True:
                if not self.mount_code_exists:
                    assert image == None  # because we are creating a new image, so cannot overrule
                    image = self._internal_image_save(stop=True)
            elif mount == False:
                if self.mount_code_exists:
                    assert image == None
                    image = self._internal_image_save(stop=True)

        if self.container_exists_in_docker:
            start_cmd = f"docker start {self.config.name}"
            self._tools.execute(start_cmd, interactive=False)
            return

        if not image:
            image = self.config.image
        if ":" in image:
            image = image.split(":")[0]

        if self.isrunning():
            # means we did not start because of any mismatch, so we can return
            # if people want to make sure its new situation they need to force a stop
            if update or ssh:
                self._update(update=update, ssh=ssh)
            return

        # Now create the container
        DIR_CODE = self._my.config["DIR_CODE"]
        DIR_BASE = self._my.config["DIR_BASE"]

        MOUNTS = ""
        if mount:
            MOUNTS = f"""
            -v {DIR_CODE}:/sandbox/code \
            -v {DIR_BASE}/myhost:/sandbox/myhost
            """
            MOUNTS = self._tools.text_strip(MOUNTS)
        else:
            MOUNTS = f"-v {DIR_BASE}/myhost:/sandbox/myhost"

        if portmap:
            PORTRANGE = self.config.ports_txt
        else:
            PORTRANGE = ""

        if self._my.docker.image_name_exists(f"internal_{self.config.name}:") != False:
            image = f"internal_{self.config.name}"

        run_cmd = f"docker run --name={self.config.name} --hostname={self.config.name} -d {PORTRANGE} \
        --device=/dev/net/tun --cap-add=NET_ADMIN --cap-add=SYS_ADMIN --cap-add=DAC_OVERRIDE \
        --cap-add=DAC_READ_SEARCH {MOUNTS} {image} {self.config.startupcmd}"

        run_cmd = self._tools.text_strip(run_cmd)
        run_cmd2 = self._tools.text_replace(re.sub("\s+", " ", run_cmd))

        print(" - Docker machine gets created: ")
        # print(run_cmd2)
        self._tools.execute(run_cmd2, interactive=False)

        self._update(update=update, ssh=ssh)

        if not mount:
            # mount the code in the container to the right location to let jumpscale work
            assert self.mount_code_exists == False
            self.dexec("rm -rf /sandbox/code")
            self.dexec("mkdir -p /sandbox/code/github")
            self.dexec("ln -s /sandbox/code_org /sandbox/code/github/threefoldtech")

        self._log("start done")

    def _update(self, update=False, ssh=False):

        if True or ssh or update or not self.config.done_get("ssh"):
            print(" - Configure / Start SSH server")

            self.dexec("rm -rf /sandbox/cfg/keys", showout=False)
            self.dexec(
                "rm -f /root/.ssh/authorized_keys;/etc/init.d/ssh stop 2>&1 > /dev/null", die=False, showout=False
            )
            self.dexec("/usr/bin/ssh-keygen -A", showout=False)
            self.dexec("/etc/init.d/ssh start", showout=False)
            self.dexec("rm -f /etc/service/sshd/down", showout=False)

            # get our own loaded ssh pub keys into the container
            SSHKEYS = self._tools.execute("ssh-add -L", die=False, showout=False)[1]
            if SSHKEYS.strip() != "":
                self.dexec('echo "%s" > /root/.ssh/authorized_keys' % SSHKEYS, showout=False)
            DIR_HOME = self._my.config["DIR_HOME"]
            self._tools.execute(f"mkdir -p {DIR_HOME}/.ssh && touch {DIR_HOME}/.ssh/known_hosts", showout=False)

            # DIDNT seem to work well, next is better
            # cmd = 'ssh-keygen -f "%s/.ssh/known_hosts" -R "[localhost]:%s"' % (
            #     self._my.config["DIR_HOME"],
            #     self.config.sshport,
            # )
            # self._tools.execute(cmd)

            # is to make sure we can login without interactivity
            cmd = "ssh-keyscan -H -p %s localhost >> %s/.ssh/known_hosts" % (
                self.config.sshport,
                self._my.config["DIR_HOME"],
            )
            self._tools.execute(cmd, showout=False)

        # self.shell()

        self.dexec("mkdir -p /root/state")
        if update or not self.done_get("install_base"):
            print(" - Upgrade ubuntu")
            self.dexec("add-apt-repository ppa:wireguard/wireguard -y")
            self.dexec("apt-get update")
            self.dexec("DEBIAN_FRONTEND=noninteractive apt-get -y upgrade --force-yes")
            self.dexec("apt-get install mc git -y")
            self.dexec("apt-get install python3 -y")
            self.dexec("pip3 install redis")
            self.dexec("apt-get install wget tmux -y")
            self.dexec("apt-get install curl rsync unzip redis-server htop -y")
            self.dexec("apt-get install python3-distutils python3-psutil python3-pip python3-click -y")
            self.dexec("locale-gen --purge en_US.UTF-8")
            self.dexec("apt-get install software-properties-common -y")
            self.dexec("apt-get install wireguard -y")
            self.dexec("apt-get install locales -y")
            self.done_set("install_base")
            print(" - Upgrade ubuntu ended")

        # cmd = "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' %s" % self.name
        # rc, out, err = self._tools.execute(cmd, replace=False, showout=False, die=False)
        # if rc == 0:
        #     self.config.ipaddr = out.strip()
        #     self.config.save()

        # if self._my.docker.container_name_exists("3bot") and self.name != "3bot":
        #     d = self._my.docker.container_get("3bot")
        #     # print(" - Create route to main 3bot container")
        #     cmd = "ip route add 10.10.0.0/16 via %s" % d.config.ipaddr
        #     # TODO: why is this no longer done?

    @property
    def info(self):
        cmd = "docker inspect %s" % self.name
        rc, out, err = self._tools.execute(cmd, replace=False, showout=False, die=False)
        if rc != 0:
            raise self._tools.exceptions.Base("could not docker inspect:%s" % self.name)
        data = json.loads(out)[0]
        return data

    def dexec(self, cmd, interactive=False, die=True, showout=True):
        if "'" in cmd:
            cmd = cmd.replace("'", '"')
        if interactive:
            cmd2 = "docker exec -ti %s bash -c '%s'" % (self.name, cmd)
        else:
            cmd2 = "docker exec -t %s bash -c '%s'" % (self.name, cmd)
        self._tools.execute(cmd2, interactive=interactive, showout=showout, replace=False, die=die)

    def shell(self, cmd=None):
        if not self.isrunning():
            self.start()
        if cmd:
            self.execute("source /sandbox/env.sh;cd /sandbox;clear;%s" % cmd, interactive=True)
        else:
            self.execute("source /sandbox/env.sh;cd /sandbox;clear;bash", interactive=True)

    def diskusage(self):
        """
        uses ncdu to visualize disk usage
        :return:
        """
        self.dexec("apt update;apt install ncdu -y;ncdu /", interactive=True)

    def execute(
        self,
        cmd,
        retry=None,
        showout=True,
        timeout=3600 * 2,
        die=True,
        jumpscale=False,
        python=False,
        replace=True,
        args=None,
        interactive=True,
    ):

        self.executor.execute(
            cmd,
            retry=retry,
            showout=showout,
            timeout=timeout,
            die=die,
            jumpscale=jumpscale,
            python=python,
            replace=replace,
            args=args,
            interactive=interactive,
        )

    def kosmos(self):
        self.execute("j.shell()", interactive=True, jumpscale=True)

    def stop(self):
        if self.container_running:
            self._tools.execute("docker stop %s" % self.name, showout=False)

    def isrunning(self):
        if self.name in self._my.docker.containers_running():
            return True
        return False

    def restart(self):
        self.stop()
        self.start()

    def delete(self):
        """
        delete & remove the path with the config file to the container
        :return:
        """
        if self.container_exists_in_docker:
            self.stop()
            self._tools.execute("docker rm -f %s" % self.name, die=False, showout=False)
        self._tools.delete(self._path)
        if self._my.docker.image_name_exists(f"internal_{self.config.name}"):
            image = f"internal_{self.config.name}"
            self._tools.execute("docker rmi -f %s" % image, die=True, showout=False)
        self.config.reset()
        if self.name in self._my.docker._dockers:
            self._my.docker._dockers.pop(self.name)

    @property
    def export_last_image_path(self):
        """
        readonly returns the last image created
        :return:
        """
        path = "%s/exports/%s.tar" % (self._path, self._export_image_last_version)
        return path

    @property
    def _export_image_last_version(self):
        dpath = "%s/exports/" % self._path
        highest = 0
        for item in os.listdir(dpath):
            version = 0
            try:
                version = int(item.replace(".tar", ""))
            except:
                self._tools.delete("%s/%s" % (dpath, item))
            if version > highest:
                highest = version
        return highest

    def import_(self, path=None, name=None, image=None, version=None):
        """

        :param path:  if not specified will be {DIR_BASE}/var/containers/$name/exports/$version.tar
        :param version: version of the export, if not specified & path not specified will be last in the path
        :param image: docker image name as used by docker to import to
        :param start: start the container after import
        :param mount: do you want to mount the dirs to host
        :param portmap: do you want to do the portmappings (ssh is always mapped)
        :return:
        """
        image = self._image_clean(image)

        if not path:
            if not name:
                if not version:
                    version = self._export_image_last_version
                path = "%s/exports/%s.tar" % (self._path, version)
            else:
                path = "%s/exports/%s.tar" % (self._path, name)
        if not self._tools.exists(path):
            raise self._tools.exceptions.Operations("could not find import file:%s" % path)

        if not path.endswith(".tar"):
            raise self._tools.exceptions.Operations("export file needs to end with .tar")

        self.stop()
        self._my.docker.image_remove(image)

        print("import docker:%s to %s, will take a while" % (path, self.name))
        self._tools.execute(f"docker import {path} {image}")
        self.config.image = image

    def export(self, path=None, name=None, version=None):
        """
        :param path:  if not specified will be {DIR_BASE}/var/containers/$name/exports/$version.tar
        :param version:
        :param overwrite: will remove the version if it exists
        :return:
        """
        dpath = "%s/exports/" % self._path
        if not self._tools.exists(dpath):
            self._tools.dir_ensure(dpath)

        if not path:
            if not name:
                if not version:
                    version = self._export_image_last_version + 1
                path = "%s/exports/%s.tar" % (self._path, version)
            else:
                path = "%s/exports/%s.tar" % (self._path, name)
        if self._tools.exists(path):
            self._tools.delete(path)
        print("export docker:%s to %s, will take a while" % (self.name, path))
        self._tools.execute("docker export %s -o %s" % (self.name, path))
        return path

    def _internal_image_save(self, stop=False, image=None):
        if not image:
            image = f"internal_{self.name}"
        cmd = "docker rmi -f %s" % image
        self._tools.execute(cmd, die=False, showout=False)
        cmd = "docker rmi -f %s:latest" % image
        self._tools.execute(cmd, die=False, showout=False)
        cmd = "docker commit -p %s %s" % (self.name, image)
        self._tools.execute(cmd)
        if stop:
            self.stop()
        return image

    def _log(self, msg):
        self._tools.log(msg)

    def save(self, development=False, image=None, code_copy=False, clean=False):
        """

        :param clean: remove all files not needed for a runtime environment
        :param clean_devel: remove all files not needed for a development environment and a runtime environment
        :param image:
        :return:
        """
        image = self._image_clean(image)

        self._my.docker.image_remove("internal_%s" % self.config.name)

        def export_import(image, start=True):
            image2 = image.replace("/", "_")
            image2 = self._image_clean(image2)
            self.export(name=image2)
            self.import_(name=image2)
            self.start(mount=False)

        if code_copy:
            self._log("copy code")
            self.execute(self._my.installers.base.code_copy_script_get())

        if clean:
            if self.mount_code_exists:
                self._log("save first, before start again without mounting")
                self._update()
                self._internal_image_save()
                self.stop()
                self.start(mount=False, update=False)
            # wait for docker to start and ssh become available
            time.sleep(10)
            self.execute(self._my.installers.base.cleanup_script_get(), die=False)
            self.dexec("umount /sandbox/code", die=False)
            self.dexec("rm -rf /sandbox/code")

            if development:
                export_import("%s_dev" % image)
                self._internal_image_save(image="%s_dev" % image)

            self.execute(self._my.installers.base.cleanup_script_developmentenv_get(), die=False)

            self._my.docker.image_remove("internal_%s" % self.config.name)
            self._my.docker.image_remove("internal_%s_dev" % self.config.name)

            export_import(image=image)

        else:
            self._update()
            self._internal_image_save()

        self._my.docker.image_remove("internal_%s" % self.config.name)

        self.config.save()

        # remove authorized keys
        self.dexec("rm -f /root/.ssh/*")
        self._internal_image_save(image=image)

        self.stop()
        self.delete()

    def push(self, image=None):
        if not image:
            image = self.image
        cmd = "docker push %s" % image
        self._tools.execute(cmd)

    def _install_tcprouter(self):
        """
        Install tcprouter builder to be part of the image
        """
        self.execute(". /sandbox/env.sh; kosmos 'j.builders.network.tcprouter.install()'")

    def _install_package_dependencies(self):
        # self.execute("j.tools.threebot_packages._children.threefold__wikis.install()", jumpscale=True)
        self._tools.shell()

    # def config_jumpscale(self):
    #     ##no longer ok, intent was to copy values from host but no longer the case
    #     CONFIG = {}
    #     for i in [
    #         "USEGIT",
    #         "DEBUG",
    #         "LOGGER_INCLUDE",
    #         "LOGGER_EXCLUDE",
    #         "LOGGER_LEVEL",
    #         # "LOGGER_CONSOLE",
    #         # "LOGGER_REDIS",
    #         "SECRET",
    #     ]:
    #         if i in self._my.config:
    #             CONFIG[i] = self._my.config[i]
    #     self._tools.config_save(self._path + "/cfg/jumpscale_config.toml", CONFIG)
    #

    def install_jumpscale(
        self,
        secret=None,
        force=False,
        threebot=False,
        pull=False,
        redo=False,
        reset=False,
        identity=None,
        email=None,
        words=None,
    ):

        if not force:
            if not self.executor.state_exists("STATE_JUMPSCALE"):
                force = True

        if not force and threebot:
            if not self.executor.state_exists("STATE_THREEBOT"):
                force = True

        # if identity == "build":
        #     secret = "build"

        if not secret:
            secret = self._my.secret_get()

        args_txt = ""
        if redo:
            args_txt += " -r"
        if threebot:
            args_txt += " --threebot"
        if pull:
            args_txt += " --pull"
        if reset:
            args_txt += " --reset"
        if email:
            args_txt += f" --email={email}"
        if words:
            args_txt += f" --words='{words}'"

        if not self._my.interactive:
            args_txt += " --no-interactive"
        if identity:
            args_txt += f" -i {identity}"

        dirpath = os.path.dirname(inspect.getfile(self._tools.__class__))
        jsxfile = os.path.join(dirpath, "jsx")
        if not os.path.exists(jsxfile):
            self.execute(
                """
            rm -f /tmp/jsx
            ln -s /sandbox/code/github/threefoldtech/jumpscaleX_core/install/jsx.py /tmp/jsx
            """
            )
        else:
            raise self._tools.exceptions.Base("not implemented, need to get more files over full corelib")
            print(" - copy installer over from where I install from")
            for item in ["jsx", "Installself._tools.py"]:
                src1 = "%s/%s" % (dirpath, item)
                self.executor.upload(src1, "/tmp")

        # python3 jsx configure --sshkey {self._my.sshagent.key_default_name} -s
        # WHY DO WE NEED THIS, in container ssh-key should always be there & loaded, don't think there is a reason to configure it

        cmd = f"""
        cd /tmp
        #next will start redis and make sure secret is in there
        python3 jsx secret {secret} 
        """
        print(" - Configure secret ")
        # best to set the secret first because otherwise we cannot be sure bcdb will work
        self.execute(cmd)

        cmd = f"""
        cd /tmp
        python3 jsx install {args_txt}
        """
        print(" - Installing jumpscaleX ")
        self.execute(cmd)

        print(" - Install succesfull")

        self.executor.state_set("STATE_JUMPSCALE")
        if threebot:
            self.executor.state_set("STATE_THREEBOT")

    def install_jupyter(self):
        self.execute(". /sandbox/env.sh; kosmos 'j.servers.notebook.install()'")

    def zerotier_connect(self):
        if not self.executor.state_exists("zerotier_installed"):
            self.execute("curl -s https://install.zerotier.com | sudo bash", die=False)
            self.executor.state_set("zerotier_installed")
        if not self.executor.state_exists("zerotier_joined"):
            self.execute("killall zerotier-one 2>&1 > /dev/null;zerotier-one -d")
            self.execute("zerotier-cli join 35c192ce9b01847c", die=False)
            self.executor.state_set("zerotier_joined")

        addr = None
        while not addr:
            print("waiting for zerotier to become live")
            rc, out, err = self.executor.execute("zerotier-cli listnetworks -j")
            self._tools.clear()
            print("WAITING FOR ZEROTIER")
            print(out)
            r = json.loads(out)
            if len(r) == 1:
                r = r[0]
                if "assignedAddresses" in r:
                    addr = r["assignedAddresses"]
                    if len(addr) > 0:
                        addr = addr[0].split("/", 1)[0]
            else:
                self.execute("zerotier-cli join 35c192ce9b01847c", die=False)

        print(" - IP ADDRESS OF YOUR CONTAINER: %s" % addr)

        return addr

    def __repr__(self):
        return "# CONTAINER: \n %s" % self._tools._data_serializer_safe(self.config.__dict__)

    __str__ = __repr__

    @property
    def wireguard(self):
        if not self._wireguard:
            self._wireguard = WireGuardServer(addr="127.0.0.1", port=self.config.sshport, myid=199)
        return self._wireguard
