import jsx


def stop(name="simulator"):
    """
    Stop simulator
    """
    jsx.container_stop.callback(name)


def start(name="simulator"):
    """
    Start simulator
    """
    jsx.tfgrid_simulator.callback(name)


def shell(name="simulator"):
    """
    Shell for simulator
    """
    jsx.container_shell.callback(name)


def kosmos(name="simulator"):
    """
    Start kosmos shell on simulator
    """
    jsx.kosmos.callback(name)
