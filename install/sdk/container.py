from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args

_containers = SDKContainers(core=core, args=args)

__all__ = ["install", "stop", "start", "shell", "kosmos", "list"]


def _containers_do(prefix=None, delete=False, stop=False):
    for item in _containers.IT.DockerFactory.list():
        if prefix == "":
            prefix = None
        if prefix:
            if not item.startswith(prefix):
                continue
        if delete or stop:
            d = _containers.IT.DockerFactory.container_get(item)
            if stop:
                print(f" - STOP: {item}")
                d.stop()
            if delete:
                print(f" - DELETE: {item}")
                d.delete()


def install(name=None, testnr=None, identity=None, delete=False, mount=True, email=None, words=None):
    """

    identity is the name of your threebot

    create the 3bot container and install jumpscale inside
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    @param testnr: if not Null the identity will become: $your3botname$testnr.test,
        secret for that container will be test
        email will be also predefined, and you will become admin automatically in the 3bot

    """
    delete = core.IT.Tools.bool(delete)
    mount = core.IT.Tools.bool(mount)

    if email:
        args.email = email
    if words:
        args.words = words

    import pudb

    pu.db
    if testnr:
        testnr = int(testnr)
        identity_you = _containers._identity_ask(identity)
        email = f"test{testnr}@{identity_you}"
        identity_you = identity_you.split(".", 1)[0]
        identity = f"{identity_you}{testnr}.test"

    c = _containers.get(identity=identity, name=name, delete=delete, mount=mount, email=email)


def shell(name=None):
    """
    Shell
    """
    c = _containers.get(name=name)
    c.shell()


def kosmos(name=None):
    """
    Start kosmos shell
    """
    c = _containers.get(name=name)
    c.kosmos()


def list():
    """
    list the containers
    """
    _containers_do()


def start(name=None):
    """
    """
    c = _containers.get(name=name)
    c.start()


def stop(name=None):
    """
    stop specified containers, can use * in name
    if name not specified then its current container
    """
    if name and "*" in name:
        prefix = name.replace("*", "")
        _containers_do(prefix=prefix, delete=False, stop=True)
    elif name == None:
        _containers_do(delete=False, stop=True)
    else:
        c = _containers.get(name=name)
        c.stop()


def delete(name=None):
    """
    delete specified containers, can use * in name
    if name not specified then its current container
    """
    if name and "*" in name:
        prefix = name.replace("*", "")
        _containers_do(prefix=prefix, delete=True, stop=False)
    elif name == None:
        _containers_do(delete=True, stop=False)
    else:
        _containers.delete(name=name)
