"""manage simulator"""
from .container import _containers, _threebot_browser
from .container import install as _install_container
from .container import delete as _delete_container

__all__ = ["browser", "stop", "start", "shell", "restart"]


def start(delete=False, browser_open=True, code_update_force=True, zerotier=False):
    """
    install & run a container with SDK & simulator
    a connection to zerotier network will be made

    param: code_update_force be careful, will remove your code changes

    """
    if delete:
        _delete_container("simulator")
        code_update_force = True

    if not _containers.IT.DockerFactory.container_name_exists("simulator"):
        _install_container("simulator", delete=delete, code_update_force=code_update_force, pull=True, zerotier=zerotier, explorer="none")
        c = _containers.get(name="simulator", explorer="none")
        c.execute("j.tools.tfgrid_simulator.start()", jumpscale=True)
    else:
        c = _containers.get(name="simulator", explorer="none")

    if browser_open:
        browser()


def stop():
    """
    stop simulator & remove the container
    """
    _delete_container("simulator")


def browser():
    """
    connect browser to your jupyter, make sure its not open yet
    """
    c = _containers.get(name="simulator")
    httpnb = 5000 + int(c.config.portrange) * 10
    url = f"http://localhost:{httpnb}"
    _threebot_browser(c, url=url)
    print(f" - CONNECT TO YOUR SIMULATOR ON: {url}")


def restart(browser_open=False):
    """
    restart the simulator, this can help to remove all running kernels
    the pyjupyter notebook can become super heavy
    """
    if not _containers.IT.DockerFactory.container_name_exists("simulator"):
        start()
    else:
        c = _containers.get(name="simulator")
        c.execute("j.tools.tfgrid_simulator.stop()", jumpscale=True)
        c.execute("j.tools.tfgrid_simulator.start()", jumpscale=True)

    if browser_open:
        browser()


def shell():
    """
    get a shell into the simulator
    """
    if not _containers.IT.DockerFactory.container_name_exists("simulator"):
        start()
    c = _containers.get(name="simulator")
    c.shell()
