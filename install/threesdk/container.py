"""manage containers"""
from .lib.SDKContainers import SDKContainers
from .core import core
from .args import args


_containers = SDKContainers(core=core, args=args)

__all__ = ["install", "stop", "start", "shell", "kosmos", "list", "delete"]


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
            _containers.delete(name=item)


def install(
    name=None,
    testnr=None,
    identity=None,
    delete=False,
    email=None,
    words=None,
    server=False,
    zerotier=False,
    pull=True,
    secret=None,
    explorer=None,
    code_update_force=False,
):
    """
    create the 3bot container and install jumpscale inside

    identity is the name of your threebot
    arguments left empty will be asked interactively

    testnr: if not Null the identity will become: $your3botname$testnr.test,
      secret for that container will be test
      email will be also predefined, and you will become admin automatically in the 3bot
      words should be retrieved from 3bot connect app to be used for encryption

    """
    delete = core.IT.Tools.bool(delete)

    if code_update_force:
        pull = True

    if identity:
        if identity != args.identity and args.identity:
            args.reset()
        args.identity = identity

    if email:
        args.email = email
    if words:
        args.words = words
    if secret:
        args.secret = secret

    if testnr:
        testnr = int(testnr)
        identity_you = _containers._identity_ask(identity)
        email = f"test{testnr}@{identity_you}"
        identity_you = identity_you.split(".", 1)[0]
        identity = f"{identity_you}{testnr}.test"
        name = f"test{testnr}"

    c = _containers.get(
        identity=identity,
        name=name,
        delete=delete,
        email=email,
        pull=pull,
        code_update_force=code_update_force,
        words=words,
        secret=secret,
        explorer=explorer,
    )

    if zerotier:
        addr = c.zerotier_connect()
        print(f" - CONNECT TO YOUR 3BOT ON: https://{addr}:4000/")

    if server:
        _server(c)


def shell(name=None):
    """
    shell into your container
    """
    name = _containers._name(name)
    _containers.assert_container(name)
    c = _containers.get(name=name, explorer="none")
    c.shell()


def kosmos(name=None):
    """
    start kosmos shell
    """
    name = _containers._name(name)
    _containers.assert_container(name)
    c = _containers.get(name=name, explorer="none")
    c.kosmos()


def list():
    """
    list the containers
    """
    _containers_do()


def start(name=None, server=False, browser_open=True):
    """
    @param server=True will start 3bot server
    """
    server = core.IT.Tools.bool(server)
    c = _containers.get(name=name)
    c.start()
    if server:
        _server(c, browser_open)
    return c


def _server(c, browser_open=True):
    c.execute("source /sandbox/env.sh;3bot start")
    if browser_open:
        _threebot_browser(c)


def _threebot_browser(c, url=None):

    if not url:
        https = 4000 + int(c.config.portrange) * 10
        url = f"https://localhost:{https}/"

    if core.IT.MyEnv.platform_is_osx:
        cmd = (
            'open -n -a /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
                --args --user-data-dir="/tmp/chrome_dev_test" --disable-web-security --ignore-certificate-errors %s'
            % url
        )
        core.IT.Tools.execute(cmd)

    try:
        import webbrowser
        webbrowser.open_new_tab(url)
    except:
        pass

    return url


def stop(name=None):
    """
    stop specified containers, can use * in name
    if name not specified then its current container
    """
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
    docker = _containers.get(name=name)
    wg = docker.wireguard
    if not connect:
        wg.disconnect()
    else:
        wg.reset()
        wg.server_start()
        wg.connect()
        print(wg)


def zerotier(name=None, connect=False):
    """
    enable zerotier server inside your container
    if connect will use local zerotier tools to make the connection to same network

    its using a predefined range in which all SDK's will be connected if zerotier enabled

    """
    c = _containers.get(name=name)
    if connect:
        addr = c.zerotier_connect()
        print(f" - CONNECT TO YOUR 3BOT ON: https://{addr}:4000/")
