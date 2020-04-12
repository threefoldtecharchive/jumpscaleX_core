from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args

_containers = SDKContainers(core=core, args=args)

__all__ = ["install", "stop", "start", "shell", "kosmos", "list"]


def containers_do(prefix=None, delete=False, stop=False):
    for item in _containers.IT.DockerFactory.list():
        if prefix == "":
            prefix = None
        if prefix:
            if not item.startswith(prefix):
                continue
        if delete or stop:
            d = _containers.DockerFactory.container_get(item)
            if stop:
                print(f" - STOP: {item}")
                d.stop()
            if delete:
                print(f" - DELETE: {item}")
                d.delete()


def _identity_ask(identity=None):
    if not identity and args.identity:
        return args.identity
    if not identity:
        identity = core.IT.Tools.ask_string("what is your threebot name?")
    if "." not in identity:
        identity += ".3bot"
    identity = identity.lower()
    if args.identity != identity:
        args.identity = identity
        args.words = None
        args.email = None


def install(name=None, identity=None, reset=False, mount=True, email=None, words=None):
    """

    identity is the name of your threebot

    create the 3bot container and install jumpscale inside
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """
    reset = core.IT.Tools.bool(reset)
    mount = core.IT.Tools.bool(mount)
    _identity_ask(identity)
    if email:
        args.email = email
    if words:
        args.words = words
    c = _containers.get(name=name, reset=reset, mount=mount)


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
    containers_do()


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
        containers_do(prefix=prefix, delete=False, stop=True)
    elif name == None:
        containers_do(delete=False, stop=True)
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
        containers_do(prefix=prefix, delete=True, stop=False)
    elif name == None:
        containers_do(delete=True, stop=False)
    else:
        _containers.delete(name=name)
