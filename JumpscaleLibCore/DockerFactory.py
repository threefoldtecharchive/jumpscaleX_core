import shutil
from Docker import DockerContainer
import os


class DockerFactory:
    def __init__(self, myenv):
        self._my = myenv
        self._tools = myenv.tools
        self._init = False
        self._dockers = {}

    def indocker(self):
        """
        will check if we are in a docker
        :return:
        """
        rc, out, _ = self._tools.execute("cat /proc/1/cgroup", die=False, showout=False)
        if rc == 0 and out.find("/docker/") != -1:
            return True
        return False

    def init(self, name=None):
        if not self._init:
            rc, out, _ = self._tools.execute("cat /proc/1/cgroup", die=False, showout=False)
            if rc == 0 and out.find("/docker/") != -1:
                # nothing to do we are in docker already
                return

            if self._my.platform() == "linux" and not self._tools.cmd_installed("docker"):
                self._my.installers.ubuntu.docker_install()
                self._tools._cmd_installed["docker"] = shutil.which("docker")

            if not self._tools.cmd_installed("docker"):
                raise self._tools.exceptions.Operations("Could not find Docker installed")

            self._init = True
            cdir = self._tools.text_replace("{DIR_BASE}/var/containers")
            self._tools.dir_ensure(cdir)
            for name_found in os.listdir(cdir):
                if not os.path.isdir(os.path.join(cdir, name_found)):
                    # https://github.com/threefoldtech/jumpscaleX_core/issues/297
                    # in case .DS_Store is created when opened in finder
                    continue
                # to make sure there is no recursive behaviour if called from a docker container
                if name_found != name and name_found.strip().lower() not in ["shared"]:
                    DockerContainer(self._my, name_found)

    def container_delete(self, name):
        self.init()
        assert name
        assert len(name) > 3
        if name in self._dockers:
            docker = self._dockers[name]
            docker.delete()
            if name in self._dockers:
                self._dockers.pop(name)

    def container_get(
        self, name, image="threefoldtech/3bot2", start=False, delete=False, ports=None, mount=True, pull=False
    ):
        self.init()
        assert name
        assert len(name) > 3
        if delete and name in self._dockers:
            docker = self._dockers[name]
            docker.delete()
            # needed because docker object is being retained
            docker.config.save()
            if name in self._dockers:
                self._dockers.pop(name)

        docker = None
        if name in self._dockers:
            docker = self._dockers[name]
            if docker.container_running:
                if mount:
                    if docker.info["Mounts"] == []:
                        # means the current docker has not been mounted
                        docker.stop()
                        docker.start(mount=True)
                else:
                    if docker.info["Mounts"] != []:
                        docker.stop()
                        docker.start(mount=False)
                return docker
        if not docker:
            docker = DockerContainer(self._my, name=name, image=image, ports=ports)
        if start:
            docker.start(mount=mount, pull=pull)
        return docker

    def containers_running(self):
        names = self._tools.execute("docker ps --format='{{json .Names}}'", showout=False, replace=False)[1].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    def containers_names(self):
        names = self._tools.execute("docker container ls -a --format='{{json .Names}}'", showout=False, replace=False)[
            1
        ].split("\n")
        names = [i.strip("\"'") for i in names if i.strip() != ""]
        return names

    def containers(self):
        self.init()
        return self._dockers.values()

    def list(self):
        res = []
        for d in self.containers():
            print(" - %-10s : %-15s : %-25s (sshport:%s)" % (d.name, d.config.ipaddr, d.config.image, d.config.sshport))
            res.append(d.name)
        return res

    def container_name_exists(self, name):
        return name in self.containers_names()

    def image_names(self):
        names = self._tools.execute("docker images --format='{{.Repository}}:{{.Tag}}'", showout=False, replace=False)[
            1
        ].split("\n")
        res = []
        for name in names:
            name = name.strip()
            name = name.strip("\"'")
            name = name.strip("\"'")
            if name == "":
                continue
            if ":" in name:
                name = name.split(":", 1)[0]
            res.append(name)

        return res

    def image_name_exists(self, name):
        if ":" in name:
            name = name.split(":")[0]
        return name in self.image_names()

    def image_remove(self, name):
        if name in self.image_names():
            self._tools.log("remove container:%s" % name)
            self._tools.execute("docker rmi -f %s" % name)

    def reset(self, images=True):
        """
        jsx containers-reset

        will stop/remove all containers
        if images==True will also stop/remove all images
        :return:
        """
        for name in self.containers_names():
            d = self.container_get(name)
            d.delete()

        # will get all images based on id
        names = self._tools.execute("docker images --format='{{.ID}}'", showout=False, replace=False)[1].split("\n")
        for image_id in names:
            if image_id:
                self._tools.execute("docker rmi -f %s" % image_id)

        self._tools.delete(self._tools.text_replace("{DIR_BASE}/var/containers"))

    #
    # def get_container_port_binding(container_name="3obt", port="9001/udp"):
    #     ports_bindings = self._tools.execute(
    #         "docker inspect {container_name} --format={data}".format(
    #             container_name=container_name, data="'{{json .HostConfig.PortBindings}}'"
    #         ),
    #         showout=False,
    #         replace=False,
    #     )
    #     # Get and serialize the binding ports data
    #     all_ports_data = json.loads(ports_bindings[1])
    #     port_binding_data = all_ports_data.get(port, None)
    #     if not port_binding_data:
    #         raise self._tools.exceptions.Input(
    #             f"Error happened during parsing the binding ports data from container {conitainer_name} and port {port}"
    #         )
    #
    #     host_port = port_binding_data[-1].get("HostPort")
    #     return host_port

    #
    # def container_running_with_udp_ports_wireguard():
    #     containers_ports = dict()
    #     containers_names = self.containers_names()
    #     for name in containers_names:
    #         port_binding = self.get_container_port_binding(container_name=name, port="9001/udp")
    #         containers_ports[name] = port_binding
    #     return containers_ports

    def get_container_ip_address(self, container_name="3bot"):
        container_ip = self._tools.execute(
            "docker inspect {container_name} --format={data}".format(
                container_name=container_name, data="'{{json .NetworkSettings.Networks.bridge.IPAddress}}'"
            ),
            showout=False,
            replace=False,
        )[1].split("\n")
        if not container_ip:
            raise self._tools.exceptions.Input(
                f"Error happened during parsing the container {container_name} ip address data "
            )
        # Get the data in the required format
        formatted_container_ip = container_ip[0].strip("\"'")
        return formatted_container_ip

    def containers_running_ip_address(self):
        containers_ip_addresses = dict()
        containers_names = self.containers_names()
        for name in containers_names:
            container_ip = self.get_container_ip_address(container_name=name)
            containers_ip_addresses[name] = container_ip
        return containers_ip_addresses
