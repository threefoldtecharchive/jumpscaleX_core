import jsx


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
    jsx.container_install.callback(name, scratch, delete, threebot, image, branch, reinstall, no_interactive, pull, develop, nomount, ports, identity)


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
