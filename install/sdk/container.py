import jsx


def install(
    name="3bot",
    delete=False,
    count=1,
    net="172.0.0.0/16",
    identity=None,
    server=False,
    pull=False,
    update=False,
    secret=None,
):
    """
    create the 3bot container and install jumpcale inside
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """
    jsx.container.callback(name, delete, count, net, identity, server, pull, update, secret)


def stop(name="3bot"):
    """
    Stop
    """
    jsx.container_stop.callback(name)


def start(name="3bot"):
    """
    Start
    """
    jsx.container_start.callback(name)


def shell(name="3bot"):
    """
    Shell
    """
    jsx.container_shell.callback(name)


def kosmos(name="3bot"):
    """
    Start kosmos shell
    """
    jsx.kosmos(name)
