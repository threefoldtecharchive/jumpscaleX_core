"""container operations"""

from . import IT, e, container_get

__all__ = ["get", "import_by_name", "export", "build", "install"]


def get(name="3bot", delete=False, jumpscale=True, install=False, mount=True):
    IT.MyEnv.sshagent.key_default_name
    e.DF.init()
    docker = e.DF.container_get(name=name, image="threefoldtech/3bot2", start=True, delete=delete, mount=mount)
    # print(docker.executor.config)
    force = False
    if not docker.executor.exists("/sandbox/cfg/keys/default/key.priv"):
        jumpscale = True
        install = True
        force = True
    if jumpscale:
        installer = IT.JumpscaleInstaller()
        installer.repos_get(pull=False)
        if install:
            docker.install_jumpscale(force=force)
    return docker


def import_by_name(name="3bot", path=None, imagename="threefoldtech/3bot2", no_start=False):
    """
    import container from image file, if not specified will be /tmp/3bot2.tar
    :param args:
    :return:
    """
    docker = container_get(delete=True, name=name)
    docker.import_(path=path, image=imagename)
    if not no_start:
        docker.start()


def export(name="3bot", path=None, version=None):
    """
    export the 3bot to image file, if not specified will be /tmp/3bot2.tar
    :param name:
    :param path:
    :return:
    """
    _configure()
    docker = container_get(name=name)
    docker.export(path=path, version=version)


def _save(name="3bot", code_copy=False, push=False, image=None, development=False, clean=False):
    """
    starts from an export, if not there will do the export first
    :param name:
    :param path:
    :return:
    """
    if not image:
        image = "threefoldtech/3bot2"
    _configure()
    docker = container_get(name=name)
    # docker.install_jumpscale(branch=branch, force=reinstall, pull=pull, threebot=threebot)
    docker.save(image=image, development=development, code_copy=code_copy, clean=clean)
    if push:
        docker.push()


def build():
    pass


def install(
    name="3bot",
    scratch=False,
    delete=True,
    threebot=False,
    image=None,
    branch=None,
    reinstall=False,
    no_interactive=False,
    pull=False,
    develop=False,
    nomount=False,
    ports=None,
    identity=None,
):
    """
    create the 3bot container and install jumpcale inside
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """
    new_identity = None
    identities_path = os.path.join(IT.MyEnv.config["DIR_VAR"], "containers/shared/keys")
    if identity:
        identity = _name_clean(identity)
        identity_path = os.path.join(identities_path, identity)
        if not os.path.exists(identity_path):
            if no_interactive:
                raise RuntimeError("Couldn't find specified identity: {}".format(identity_path))
            if not IT.Tools.ask_yes_no("Create new identity with name {}".format(identity)):
                return
            new_identity = identity
            identity = None
        else:
            identity_contents = os.listdir(identity_path)
            if "key.priv" not in identity_contents or "conf.toml" not in identity_contents:
                raise RuntimeError(
                    "Need to have both `secret` file containing private key secret and `key.priv` for the private key"
                )
    elif os.path.exists(identities_path):
        found_identities = os.listdir(identities_path)
        if len(found_identities) > 1:
            if no_interactive:
                raise RuntimeError(
                    "Found multiple shared identities please start installation interactively or specify an identity"
                )
            identity = IT.Tools.ask_choices("Choose an identity to start container with", found_identities)
        else:
            identity = found_identities[0]

    mount = not nomount

    _configure(no_interactive=no_interactive, set_secret=not identity)

    if scratch:
        image = "threefoldtech/base2"
        if scratch:
            delete = True
        reinstall = True
    if not image:
        if not develop:
            image = "threefoldtech/3bot2"
        else:
            image = "threefoldtech/3bot2dev"

    portmap = None
    if ports:
        portmap = dict()
        for port in ports:
            src, dst = port.split(":", 1)
            portmap[src] = dst

    docker = e.DF.container_get(name=name, delete=delete, image=image, ports=portmap)

    docker.start(mount=mount, ssh=True)

    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=False, branch=branch)

    if not docker.executor.exists("/sandbox/cfg/keys/default/key.priv"):
        reinstall = True

    docker.install_jumpscale(branch=branch, force=reinstall, pull=pull, threebot=threebot, identity=identity)

    identity = identity or new_identity
    if identity:
        threebot_name = '"{}"'.format(identity)
        docker.execute(
            "source /sandbox/env.sh && kosmos 'j.tools.threebot.init_my_threebot(interactive={}, name={})'".format(
                not no_interactive, threebot_name
            )
        )


def shell(name="3bot", delete=False, nomount=False):
    """
    open a  shell to the container for 3bot
    :param name: name of container if not the default
    :return:
    """
    mount = not nomount
    docker = container_get(name=name, delete=delete, mount=mount, install=False, jumpscale=True)
    httpport = docker.config.portrange * 10 + 7000
    msg = f"""
    WELCOME TO YOUR INSTALLED LOCAL KOSMOS ENVIRONMENT (THREEBOT)

    some tips to get started

    - kosmos  : to get shell into the environment
    - 3bot    : to start/stop a 3bot ...
    - tmux a  : to see the parallel processes running (ctrl b 1 to e.g. go to panel 1)
    - htop    : to see which processes are taking how much resource
    - go to your local machine and use browser to go to: http://localhost:{httpport}/ will show webinterface

    """

    docker.shell("echo '%s';bash" % IT.Tools.text_replace(msg))
