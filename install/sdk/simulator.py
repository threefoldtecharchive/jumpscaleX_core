"""manage simulator"""
# from .args import args
from .container import _containers, _threebot_browser
from .container import install as _install_container
from .container import delete as _delete_container

# from .container import stop as _stop_container

__all__ = ["browser", "stop", "start", "shell", "restart"]


def start(delete=False, browser_open=True, pull=True, code_update_force=False):
    """
    install & run a container with SDK & simulator

    param: code_update_force be careful, will remove your code changes

    """
    if delete:
        _delete_container("simulator")

    if not DockerFactory.container_name_exists("simulator"):
        _install_container("simulator", delete=delete, code_update_force=code_update_force, pull=pull)
        c = _containers.get(name="simulator")
        c.execute("j.tools.tfgrid_simulator.start()", jumpscale=True)
    else:
        c = _containers.get(name="simulator")

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
    if not DockerFactory.container_name_exists("simulator"):
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
    if not DockerFactory.container_name_exists("simulator"):
        start()
    c = _containers.get(name="simulator")
    c.shell()


def monitor():
    """
    monitor the resources of your container
    there needs to be enough free memory and cpu resources
    """
    c = _containers.get(name="simulator")
    c.execute("htop", interactive=True, showout=False)
