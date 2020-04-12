class SDKContainers:
    def __init__(self, core, args):
        self.container = None
        self.image = "threefoldtech/3bot2"
        self.IT = core.IT
        self.core = core
        self.args = args

    def _name(self, name):
        if name:
            if self.container.name != name:
                self.container = None
        else:
            if self.container:
                name = self.container.name
            else:
                name = self.IT.Tools.ask_string("name of the container (default 3bot):", default="3bot")
        return name

    def delete(self, name=None):
        name = self._name(name)
        docker = self.IT.DockerFactory.container_get(name=name, image=self.image, start=False, delete=True)
        return docker

    def get(self, name=None, reset=False, mount=True):
        """
        """
        name = self._name(name)

        if self.container and not reset:
            return self.container

        # need to make sure 1 sshkey has been created, does not have to be in github
        self.IT.MyEnv.sshagent.key_default_name

        self.IT.DockerFactory.init()

        if name.startswith("test"):
            self.args.secret = "test"
        else:
            if not self.args.secret:
                self.IT.Tools.ask_secret("specify secret passphrase please:")

        docker = self.IT.DockerFactory.container_get(name=name, image=self.image, start=True, delete=reset, mount=mount)

        if not docker.executor.exists("/sandbox/cfg/.configured"):

            installer = self.IT.JumpscaleInstaller()
            installer.repos_get(pull=False, branch=self.core.branch)

            docker.install_jumpscale(
                force=reset,
                reset=reset,
                secret=self.args.secret,
                identity=self.args.identity,
                email=self.args.email,
                words=self.args.words,
            )

            docker.executor.file_write("/sandbox/cfg/.configured", "")

        self.container = docker
        return docker
