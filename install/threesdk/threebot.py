"""manage threebot"""
from . import container as _container

_containers = _container._containers

__all__ = ["browser", "stop", "start", "shell", "restart"]
_NAME = "3bot"


def start(delete=False, browser_open=True):
    """
    install & run a container with threebot

    param: code_update_force be careful, will remove your code changes

    """
    if delete:
        _container.delete(_NAME)

    _container.start(_NAME, True, browser_open=browser_open)


def stop():
    """
    stop 3bot
    """
    _container.stop(_NAME)


def browser():
    """
    connect browser to your 3bot, make sure its not open yet
    """
    c = _containers.get(name=_NAME)
    url = _container._threebot_browser(c)
    print(f" - CONNECT TO YOUR 3bot ON: {url}")


def delete():
    """
    Delete threebot and it's data

    Can be used when switching branches
    """
    _container.delete(_NAME)


def restart(browser_open=False, container=False):
    """
    restart the 3bot

    When passing container=True the entire container will be restart
    Could be usefull incase of trouble or high memory useage
    """
    if not _containers.IT.DockerFactory.container_name_exists(_NAME):
        start()
    else:
        if container:
            stop()
            start()
        else:
            c = _containers.get(_NAME)
            c.execute("source /sandbox/env.sh;3bot stop")
            c.execute("source /sandbox/env.sh;3bot start")

    if browser_open:
        browser()


def shell():
    """
    get a shell into the 3bot
    """
    _container.shell(_NAME)


def kosmos():
    """
    get a komos into the 3bot
    """
    _container.kosmos(_NAME)
