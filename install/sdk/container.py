"""manage containers"""
from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args
import time


_containers = SDKContainers(core=core, args=args)

__all__ = ["install", "stop", "start", "shell", "kosmos", "list", "threebot", "delete"]


def _containers_do(prefix=None, delete=False, stop=False):
    for item in _containers.IT.DockerFactory.list():
        if prefix == "":
            prefix = None
        if prefix:
            if not item.startswith(prefix):
                continue
        if stop:
            d = _containers.IT.DockerFactory.container_get(item)
            print(f" - STOP: {item}")
            d.stop()
        if delete:
            print(f" - DELETE: {item}")
            d = _containers.IT.DockerFactory.container_delete(item)


def install(
    name=None,
    testnr=None,
    identity=None,
    delete=False,
    mount=True,
    email=None,
    words=None,
    server=False,
    zerotier=False,
    pull=False,
):
    """
    create the 3bot container and install jumpscale inside

    identity is the name of your threebot

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

    if testnr:
        # core.IT.Tools.shell()
        testnr = int(testnr)
        identity_you = _containers._identity_ask(identity)
        email = f"test{testnr}@{identity_you}"
        identity_you = identity_you.split(".", 1)[0]
        identity = f"{identity_you}{testnr}.test"
        name = f"test{testnr}"

    c = _containers.get(identity=identity, name=name, delete=delete, mount=mount, email=email, pull=pull)

    if zerotier:
        addr = c.zerotier_connect()
        print(f" - CONNECT TO YOUR 3BOT ON: https://{addr}:4000/")

    if server:
        _server(c)


def shell(name=None):
    """
    shell into your container
    """
    c = _containers.get(name=name)
    c.shell()


def kosmos(name=None):
    """
    start kosmos shell
    """
    c = _containers.get(name=name)
    c.kosmos()


def list():
    """
    list the containers
    """
    _containers_do()


def start(name=None, server=False):
    """
    @param server=True will start 3bot server
    """
    server = core.IT.Tools.bool(server)
    c = _containers.get(name=name)
    c.start()
    if server:
        _server(c)


def _server(c):
    c.execute("source /sandbox/env.sh;3bot start")
    _threebot_browser()


def _threebot_browser(url=None):

    if not url:
        url = "https://localhost:4000/"

    if core.IT.MyEnv.platform_is_osx:
        cmd = (
            'open -n -a /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
                --args --user-data-dir="/tmp/chrome_dev_test" --disable-web-security --ignore-certificate-errors %s'
            % url
        )
        core.IT.Tools.execute(cmd)

    # try:
    #     import webbrowser
    #
    #     core.IT.Tools.shell()
    #     # time.sleep(5)
    #     # if core.IT.MyEnv.platform_is_osx:
    #     #     webbrowser.get("safari").open_new_tab("https://localhost:4000")
    #     # else:
    #     webbrowser.open_new_tab("https://localhost:4000")
    # except:
    #     pass


def stop(name=None):
    """
    stop specified containers, can use * in name
    if name not specified then its current container
    """
    # TODO: need to make sure is saved, when starting afterwards do not have to reinstall jumpscale
    if name and "*" in name:
        prefix = name.replace("*", "")
        _containers_do(prefix=prefix, delete=False, stop=True)
    elif name is None:
        _containers_do(delete=False, stop=True)
    else:
        c = _containers.get(name=name)
        c.stop()


def delete(name=None):
    """
    delete specified containers, can use * in name
    if name not specified then its current container
    """
    _delete(name)


def _delete(name=None):

    if name and "*" in name:
        prefix = name.replace("*", "")
        _containers_do(prefix=prefix, delete=True, stop=False)
    elif name is None:
        _containers_do(delete=True, stop=False)
    else:
        _containers.delete(name=name)


def wireguard(name=None, connect=True):
    """
    enable wireguard server inside your container
    if connect will use local wireguard tools (userspace prob) if installed locally to make connection to the container
    """
    # TODO: wireguard (also test on OSX)
    # TODO: wireguard the connect & install is in 1 method
    raise RuntimeError("implement")


def threebot(delete=False, identity=None, email=None, words=None, restart=False, browser=True, pull=False):
    """
    will make sure you have your 3bot alive

    - identity is your 3bot unique name (only needed to specify once)
    - email is your email (only needed to specify once)
    - if you already have your secret key, specify the words of your key

    when 3bot becomes unresponsive you can always ask a restart on server, the container will not be restarted

    pull will update the docker image as well as the code on github

    """
    if delete:
        _delete("3bot")
    if not _containers.IT.DockerFactory.container_name_exists("3bot"):
        install("3bot", delete=delete, identity=identity, email=email, words=words, server=True, pull=pull)

    c = _containers.get(name="3bot")
    c.execute("mkdir -p /tmp/jumpscale")
    if restart:
        c.execute("source /sandbox/env.sh;3bot stop")
        c.execute("source /sandbox/env.sh;3bot start")
    if browser:
        _threebot_browser()


def zerotier(name=None, connect=False):
    """
    enable zerotier server inside your container
    if connect will use local zerotier tools to make the connection to same network

    its using a predefined range in which all SDK's will be connected if zerotier enabled

    """
    c = _containers.get(name=name)
    addr = c.zerotier_connect()
    print(f" - CONNECT TO YOUR 3BOT ON: https://{addr}:4000/")
    if connect:
        # TODO: zerotier (see what is done in simulator, use that network)
        raise RuntimeError("implement")


# def wireguard(name=None, test=False, disconnect=False):
#     """
#     jsx wireguard
#     enable wireguard, can be on host or server
#     :return:
#     """
#     docker = container_get(name=name)
#     wg = docker.wireguard
#     if disconnect:
#         wg.disconnect()
#     elif test:
#         print(wg)
#         IT.Tools.shell()
#     else:
#         wg.reset()
#         print(wg)
#         wg.server_start()
#         wg.connect()

# def connect(test=False, disconnect=False):
#     """
#     only for core developers and engineers of threefold, will connect to some core
#     infrastructure for helping us to communicate
#     :return:
#     """
#     myid = IT.MyEnv.registry.myid
#     addr = IT.MyEnv.registry.addr[0]
#     wg = IT.WireGuardServer(addr=addr, myid=myid)
#     if disconnect:
#         wg.disconnect()
#     elif test:
#         print(wg)
#         IT.Tools.shell()
#     else:
#         wg.reset()
#         print(wg)
#         wg.server_start()
#         wg.connect()
