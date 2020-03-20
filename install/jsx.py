#!/usr/bin/env python3
import click
import os
import shutil
import urllib
import requests
from urllib.request import urlopen
from importlib import util
import time


DEFAULT_BRANCH = "unstable"
os.environ["LC_ALL"] = "en_US.UTF-8"


def load_install_tools(branch=None, reset=False):
    # get current install.py directory

    path = "/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py"
    if not os.path.exists(path):
        path = os.path.expanduser("~/sandbox/code/github/threefoldtech/jumpscaleX_core/install/InstallTools.py")

    if not branch:
        branch = DEFAULT_BRANCH
    # first check on code tools
    if not os.path.exists(path):
        rootdir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(rootdir, "InstallTools.py")
        # now check on path next to jsx
        if not os.path.exists(path) or reset:  # or path.find("/code/") == -1:
            url = "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/InstallTools.py" % branch

            # fallback to default branch if installation is being done for another branch that doesn't exist in core
            if branch != DEFAULT_BRANCH and requests.get(url).status_code == 404:
                url = (
                    "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/InstallTools.py"
                    % DEFAULT_BRANCH
                )

            with urlopen(url) as resp:
                if resp.status != 200:
                    raise RuntimeError("fail to download InstallTools.py")
                with open(path, "w+") as f:
                    f.write(resp.read().decode("utf-8"))
                print("DOWNLOADED INSTALLTOOLS TO %s" % path)

    spec = util.spec_from_file_location("IT", path)
    IT = spec.loader.load_module()
    IT.MyEnv.init()
    return IT


IT = load_install_tools()
IT.MyEnv.interactive = True  # std is interactive


class JSXEnv:
    def __init__(self):
        self._DF = IT.DockerFactory

    @property
    def DF(self):
        if not self._DF:
            self._DF.init()
        return self._DF


e = JSXEnv()


def jumpscale_get(die=True):
    # jumpscale need to be available otherwise cannot do
    try:
        from Jumpscale import j
    except Exception:
        if die:
            raise RuntimeError("ERROR: cannot use jumpscale yet, has not been installed")
        return None
    return j


# have to do like this, did not manage to call the click enabled function (don't know why)
def _configure(
    codedir=None, debug=False, sshkey=None, no_sshagent=False, no_interactive=False, privatekey_words=None, secret=None
):
    interactive = not no_interactive
    sshagent_use = not no_sshagent

    IT.MyEnv.configure(
        readonly=None,
        codedir=codedir,
        sshkey=sshkey,
        sshagent_use=sshagent_use,
        debug_configure=debug,
        interactive=interactive,
        secret=secret,
    )
    j = jumpscale_get(die=False)

    if not j and privatekey_words:
        raise RuntimeError(
            "cannot load jumpscale, \
            can only configure private key when jumpscale is installed locally use jsx install..."
        )

    if j and privatekey_words:
        j.data.nacl.configure(privkey_words=privatekey_words)


"""
if not IT.MyEnv.state:
    # this is needed to make sure we can install when nothing has been done yet
    _configure()

# IT.BaseInstaller.base()
"""


@click.group()
def cli():
    pass


# CONFIGURATION (INIT) OF JUMPSCALE ENVIRONMENT
@click.command()
@click.option("--codedir", default=None, help="path where the github code will be checked out, default sandbox/code")
@click.option("--no-sshagent", is_flag=True, help="do you want to use an ssh-agent")
@click.option("--sshkey", default=None, help="if more than 1 ssh-key in ssh-agent, specify here")
@click.option("--debug", is_flag=True, help="do you want to put kosmos in debug mode?")
@click.option("-s", "--no-interactive", is_flag=True, help="default is interactive")
@click.option(
    "--privatekey",
    default=False,
    help="24 words, use '' around the private key if secret specified and private_key not then will ask in -y mode will autogenerate",
)
@click.option(
    "--secret", default=None, help="secret for the private key (to keep secret, also used for admin secret on rbot)"
)
def configure(
    codedir=None, debug=False, sshkey=None, no_sshagent=False, no_interactive=False, privatekey=None, secret=None
):
    """
    initialize 3bot (JSX) environment
    """

    return _configure(
        codedir=codedir,
        debug=debug,
        sshkey=sshkey,
        no_sshagent=no_sshagent,
        no_interactive=no_interactive,
        privatekey_words=privatekey,
        secret=secret,
    )


# INSTALL OF JUMPSCALE IN CONTAINER ENVIRONMENT
@click.command(name="container-install")
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option(
    "--scratch", is_flag=True, help="from scratch, means will start from empty ubuntu and re-install everything"
)
@click.option("-d", "--delete", is_flag=True, help="if set will delete the docker container if it already exists")
@click.option("--threebot", is_flag=True, help="also install the threebot")
@click.option(
    "-i",
    "--image",
    default=None,
    help="select the container image to use to create the container, leave empty unless you know what you do (-:",
)
@click.option(
    "-b", "--branch", default=None, help="jumpscale branch. default 'master' or 'development' for unstable release"
)
@click.option(
    "--pull",
    is_flag=True,
    help="pull code from git, if not specified will only pull if code directory does not exist yet",
)
@click.option(
    "-r",
    "--reinstall",
    is_flag=True,
    help="reinstall, basically means will try to re-do everything without removing the data",
)
# @click.option("--develop", is_flag=True, help="will use the development docker image to start from.")
@click.option("--ports", help="Expose extra ports repeat for multiple eg. 80:80", multiple=True)
@click.option("-s", "--no-interactive", is_flag=True, help="default is interactive, -s = silent")
@click.option("-nm", "--nomount", is_flag=True, help="will not mount the underlying code directory if set")
def container_install(
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
):
    """
    create the 3bot container and install jumpcale inside
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """

    IT = load_install_tools(branch=branch, reset=True)
    # IT.MyEnv.interactive = True
    # interactive = not no_interactive

    mount = not nomount

    _configure(no_interactive=no_interactive)

    if scratch:
        image = "threefoldtech/base2"
        if scratch:
            delete = True
        reinstall = True
    if not image:
        if not develop:
            image = "threefoldtech/3bot2"
        else:
            image = "threefoldtech/3bot2dev"

    portmap = None
    if ports:
        portmap = dict()
        for port in ports:
            src, dst = port.split(":", 1)
            portmap[src] = dst

    docker = e.DF.container_get(name=name, delete=delete, image=image, ports=portmap, mount=mount)

    docker.install()

    # if prebuilt:
    #     docker.sandbox_sync()

    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=False, branch=branch)

    docker.install_jumpscale(branch=branch, redo=reinstall, pull=pull, threebot=threebot)  # , prebuilt=prebuilt)

    _container_shell()


def container_get(name="3bot", delete=False, jumpscale=False, install=False, mount=True):
    IT.MyEnv.sshagent.key_default_name
    e.DF.init()
    docker = e.DF.container_get(name=name, image="threefoldtech/3bot2", start=True, delete=delete, mount=mount)
    if jumpscale:
        installer = IT.JumpscaleInstaller()
        installer.repos_get(pull=False)
        if install:
            docker.install_jumpscale()
    return docker


# INSTALL OF JUMPSCALE IN CONTAINER ENVIRONMENT
@click.command()
# @click.option("--no-sshagent", is_flag=True, help="do you want to use an ssh-agent")
@click.option("--prebuilt", is_flag=True, help="if set will allow a quick start using prebuilt threebot")
@click.option(
    "-b", "--branch", default=None, help="jumpscale branch. default 'master' or 'development' for unstable release"
)
@click.option(
    "--pull",
    is_flag=True,
    help="pull code from git, if not specified will only pull if code directory does not exist yet",
)
@click.option(
    "-r",
    "--reinstall",
    is_flag=True,
    help="reinstall, basically means will try to re-do everything without removing the data",
)
@click.option("--clean", is_flag=True, help="cleanup all data not needed")
@click.option("--threebot", is_flag=True, help="install required components for threebot")
@click.option("-s", "--no-interactive", is_flag=True, help="default is interactive, -s = silent")
def install(
    branch=None, reinstall=False, pull=False, no_interactive=False, prebuilt=False, clean=False, threebot=False
):
    """
    install jumpscale in the local system (only supported for Ubuntu 18.04+ and mac OSX, use container install method otherwise.
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '


    """
    # print("DEBUG:: no_sshagent", no_sshagent, "configdir", configdir)  #no_sshagent=no_sshagent
    IT = load_install_tools(branch=branch, reset=True)
    # IT.MyEnv.interactive = True
    _configure(no_interactive=no_interactive)
    if reinstall:
        # remove the state
        IT.MyEnv.state_reset()
        force = True
    else:
        force = False

    installer = IT.JumpscaleInstaller()
    assert prebuilt is False  # not supported yet
    installer.install(sandboxed=False, force=force, gitpull=pull, prebuilt=prebuilt, branch=branch, threebot=threebot)
    if clean:
        IT.BaseInstaller.clean(development=True)
    print("Jumpscale X installed successfully")


# INSTALL OF JUMPSCALE IN CONTAINER ENVIRONMENT
@click.command()
@click.option(
    "-b", "--branch", default=None, help="jumpscale branch. default 'master' or 'development' for unstable release"
)
@click.option(
    "--pull",
    is_flag=True,
    help="pull code from git, if not specified will only pull if code directory does not exist yet",
)
@click.option("--reset", is_flag=True, help="if reset, will remove code, be careful")
def jumpscale_code_get(branch=None, pull=False, reset=False):
    """
    install jumpscale in the local system (only supported for Ubuntu 18.04+ and mac OSX, use container install method otherwise.
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '

    """
    IT = load_install_tools(branch=branch)
    # IT.MyEnv.interactive = True
    # _configure(no_interactive=True)
    if not branch:
        branch = IT.DEFAULT_BRANCH
    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=pull, reset=reset)
    # IT.Tools.shell()


@click.command(name="container-import")
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option("-i", "--imagename", default="threefoldtech/3bot2", help="name of image where we will import to")
@click.option("-p", "--path", default=None, help="image location")
@click.option("--no-start", is_flag=True, help="container will start auto")
def container_import(name="3bot", path=None, imagename="threefoldtech/3bot2", no_start=False):
    """
    import container from image file, if not specified will be /tmp/3bot2.tar
    :param args:
    :return:
    """
    start = not no_start
    docker = container_get(delete=True, name=name)
    docker.import_(path=path, imagename=imagename, start=start)


@click.command(name="container-export")
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option("-p", "--path", default=None, help="image location")
@click.option("-v", "--version", default=None, help="image location")
def container_export(name="3bot", path=None, version=None):
    """
    export the 3bot to image file, if not specified will be /tmp/3bot2.tar
    :param name:
    :param path:
    :return:
    """
    _configure()
    docker = container_get(name=name)
    docker.export(path=path, version=version)


@click.command(name="container-save")
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option(
    "--dest", default="threefoldtech/3bot2", help="name of container image on docker hub, default threefoldtech/3bot2"
)
@click.option("-p", "--push", is_flag=True, help="push to docker hub")
@click.option("-c", "--clean", is_flag=True, help="clean runtime")
@click.option("-cd", "--cleandevel", is_flag=True, help="clean development env")
def container_save(name="3bot", dest=None, push=False, clean=False, cleandevel=False):
    """
    starts from an export, if not there will do the export first
    :param name:
    :param path:
    :return:
    """
    if not dest:
        dest = "threefoldtech/3bot2"
    _configure()
    docker = container_get(name=name)
    if cleandevel:
        clean = True
    docker.save(image=dest, clean_runtime=clean, clean_devel=cleandevel)
    if push:
        docker.push()


@click.command(name="container-stop")
@click.option("-n", "--name", default="3bot", help="name of container")
def container_stop(name="3bot"):
    """
    stop the 3bot container
    :param name:
    :return:
    """
    _configure()
    if name in e.DF.containers_running():
        docker = container_get(name=name)
        docker.stop()


@click.command(name="basebuilder")
@click.option(
    "--dest", default="threefoldtech/base2", help="name of container image on docker hub, default threefoldtech/3bot2"
)
@click.option("-p", "--push", is_flag=True, help="push to docker hub")
@click.option("-c", "--cont", is_flag=True, help="don't delete continue a previously stopped run")
def basebuilder(dest=None, push=False, cont=False):
    """
    create the base ubuntu docker which we can use as base for everything
    :param dest: default threefoldtech/base2  the base is the base ubuntu image
    :return:
    """
    delete = not cont
    basebuilder_(dest=dest, push=push, delete=delete)


def _build_phusion(push=False):
    IT = load_install_tools(branch=DEFAULT_BRANCH)
    path = IT.Tools.text_replace("{DIR_BASE}/code/github/threefoldtech/baseimage-docker")
    if not os.path.exists(path):
        IT.Tools.code_github_get(url="https://github.com/threefoldtech/baseimage-docker", branch="master")
    cmd = """
        set -ex
        cd {}/image
        docker build . -t threefoldtech/phusion:latest
    """.format(
        path
    )
    IT.Tools.execute(cmd, interactive=True)
    if push:
        IT.Tools.execute("docker pushe threefoldtech/phusion/latest")


def basebuilder_(dest=None, push=False, delete=True):
    _build_phusion(push=push)
    if not dest:
        dest = "threefoldtech/base2"
    IT = load_install_tools(branch=DEFAULT_BRANCH)
    _configure()

    # image = "threefoldtech/phusion:19.10"
    image = "threefoldtech/phusion:latest"
    docker = e.DF.container_get(name="base2", delete=delete, image=image)
    docker.install(update=True, stop=delete)
    cmd = "apt install python3-brotli python3-blosc cython3 cmake -y"
    docker.dexec(cmd)
    docker.save(image=dest, clean_runtime=True)
    if push:
        docker.push()
        if delete:
            docker.stop()
    print("- *OK* base has been built, as image & exported")


@click.command()
@click.option("-n", "--name", default=None, help="name of the wiki, you're given name")
@click.option("-u", "--url", default=None, help="url of the github wiki")
@click.option("-r", "--reset", is_flag=True, help="reset git revision and process all files")
@click.option("-f", "--foreground", is_flag=True, help="if you don't want to use the job manager (background jobs)")
def wiki_load(name=None, url=None, reset=False, foreground=False):
    # monkey patch for myjobs to start/work properly
    import gevent
    from gevent import monkey
    from Jumpscale.tools.threegit.ThreeGit import load_wiki

    import redis

    from Jumpscale import j

    try:
        threebot_client = j.clients.gedis.get("jsx_threebot", package_name="zerobot.webinterface", port=8901)
        threebot_client.ping()
        threebot_client.reload()
    except (j.exceptions.Base, redis.ConnectionError):
        print(
            "Threebot server must be running, please start a local threebot first using `kosmos -p 'j.servers.threebot.start()'`"
        )
        return

    wikis = []

    if not name or not url:
        wikis.append(
            (
                "testwikis",
                "https://github.com/threefoldtech/jumpscaleX_threebot/tree/development/ThreeBotPackages/zerobot/wiki_examples/wiki",
            )
        )
        wikis.append(("tokens", "https://github.com/threefoldfoundation/info_tokens/tree/development/docs"))
        wikis.append(("foundation", "https://github.com/threefoldfoundation/info_foundation/tree/development/docs"))
        wikis.append(("grid", "https://github.com/threefoldfoundation/info_grid/tree/development/docs"))
        wikis.append(("freeflowevents", "https://github.com/freeflownation/info_freeflowevents/tree/development/docs"))
    else:
        wikis.append((name, url))

    if not foreground:
        greenlets = [
            gevent.spawn(threebot_client.actors.wiki_content.load, wiki_name, wiki_url, reset)
            for wiki_name, wiki_url in wikis
        ]
        gevent.wait(greenlets)
    else:
        for wiki_name, wiki_url in wikis:
            load_wiki(wiki_name, wiki_url, reset=reset)
    print("You'll find the wiki(s) loaded at https://<container or 3bot hostname>/wiki")


@click.command(name="threebot-flist")
@click.option("-i", "--app_id", default=None, help="application id of it's your online")
@click.option("-s", "--secret", default=None, help="secret of it's your it's your online account")
@click.option("-u", "--username", default=None, help="username of it's your online account")
def threebot_flist(username=None, secret=None, app_id=None):
    """
    create flist of 3bot docker image
    ex: jsx threebot-flist -i APP_ID -s SECRET -u USER_NAME
    """
    if not username and not app_id and not secret:
        raise RuntimeError("should add it's your online creds")

    url = urllib.parse.urljoin("https://itsyou.online/api", "/v1/oauth/access_token")
    params = {
        "grant_type": "client_credentials",
        "client_id": app_id,
        "client_secret": secret,
        "response_type": "id_token",
        "scope": "",
        "validity": None,
    }

    resp = requests.post(url, params=params)
    resp.raise_for_status()
    jwt = resp.content.decode("utf8")

    params = {"image": "threefoldtech/3bot2:corex"}
    url = "https://hub.grid.tf/api/flist/me/docker"
    headers = {"Authorization": "Bearer %s" % jwt}
    requests.post(url, headers=headers, data=params)
    print("uploaded 3bot flist")


@click.command(name="wiki-reload")
@click.option("-n", "--name", default=None, help="name of the wiki, you're given name", required=True)
@click.option("-r", "--reset", is_flag=True, help="reset git revision and process all files")
def wiki_reload(name, reset=False):
    """
    reload the changed files from wikis repo
    ex: jsx wiki-reload -n foundation
    """
    j = jumpscale_get()
    from Jumpscale.tools.threegit.ThreeGit import reload_wiki

    try:
        reload_wiki(name, reset=reset)
    except j.exceptions.NotFound:
        print("Need to load the wiki first using wiki-load command")


@click.command(name="threebotbuilder")
@click.option("-p", "--push", is_flag=True, help="push to docker hub")
@click.option("-b", "--base", is_flag=True, help="build base image as well")
@click.option("-c", "--cont", is_flag=True, help="don't delete continue a previously stopped run")
@click.option("-nc", "--noclean", is_flag=True, help="commit the build (local save), but no cleanup or push.")
def threebotbuilder(push=False, base=False, cont=False, noclean=False):
    """
    create the 3bot and 3botdev images
    """
    delete = not cont
    if base:
        basebuilder_(push=push)
    dest = "threefoldtech/3bot2"

    IT = load_install_tools(branch=DEFAULT_BRANCH)
    _configure()

    docker = e.DF.container_get(name="3botdev", delete=delete, image="threefoldtech/base2")

    docker.install(update=delete, stop=delete)

    # we know its a ubuntu 19.10 so we can install

    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=False)

    docker.install_jumpscale(branch=DEFAULT_BRANCH, redo=delete, pull=False, threebot=True)
    docker.install_tcprouter()

    docker.image = dest

    if noclean:
        docker.save(image=dest)
        docker.delete()
    else:
        import pudb

        pu.db
        docker.save(clean_runtime=True, image=dest + "dev", code_copy=True)
        if push:
            docker.push()

        docker = e.DF.container_get(name="3bot", delete=True, image=dest + "dev")
        docker.install(update=False)
        # docker.execute("apt update") #just to make sure we have our apt-get metadata in the docker, not really needed though
        docker.save(image=dest, clean_devel=True)
        if push:
            docker.push()

    print(" - *OK* threebot container has been built, as image & exported")
    print(" - if you want to test the container do 'jsx container-shell -d'")
    print(" - if you want to push you can do 'jsx container-save -p -cd' after playing with it.")


@click.command(name="container-start")
@click.option("-n", "--name", default="3bot", help="name of container")
def container_start(name="3bot"):
    """
    start the 3bot container
    :param name:
    :return:
    """
    _configure()
    docker = container_get(name=name)
    docker.start()


@click.command(name="container-delete")
@click.option("-a", "--all", is_flag=True, help="delete all")
@click.option("-n", "--name", default="3bot", help="name of container")
def container_delete(name="3bot", all=None):
    """
    delete the 3bot container
    :param name:
    :return:
    """
    _configure()
    if all:
        for name in e.DF.containers_names():
            docker = container_get(name=name)
            docker.delete()
    else:
        if not e.DF.container_name_exists(name):
            return None
        docker = container_get(name=name)
        docker.delete()


@click.command(name="container-reset")
def containers_reset(configdir=None):
    """
    remove all docker containers & images
    :param name:
    :return:
    """
    _configure()
    e.DF.reset()


@click.command(name="containers")
def containers(configdir=None):
    """
    list the containers
    :param name:
    :return:
    """
    _configure()
    e.DF.list()


@click.command(name="container-kosmos")
@click.option("-n", "--name", default="3bot", help="name of container")
def container_kosmos(name="3bot"):
    """
    open a kosmos shell in container
    :param name: name of container if not the default =  3bot
    :return:
    """
    docker = container_get(name=name, jumpscale=True, install=False)
    os.execv(
        shutil.which("ssh"),
        [
            "ssh",
            "root@localhost",
            "-A",
            "-t",
            "-oStrictHostKeyChecking=no",
            "-p",
            str(docker.config.sshport),
            "source /sandbox/env.sh;kosmos 'print()';clear;echo WELCOME TO YOUR INTERACTIVE KOSMOS SESSION;kosmos -p",
        ],
    )


@click.command()
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option("-t", "--target", default="auto", help="auto,local,container, default is auto will try container first")
def kosmos(name="3bot", target="auto"):
    j = jumpscale_get(die=True)
    j.application.interactive = True
    n = j.data.nacl.get(load=False)  # important to make sure private key is loaded
    if n.load(die=False) is False:
        n.configure()
    j.data.bcdb.system  # needed to make sure we have bcdb running, needed for code completion
    j.shell(loc=False, locals_=locals(), globals_=globals())


@click.command(name="container-shell")
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option("-d", "--delete", is_flag=True, help="if set will delete the docker container if it already exists")
@click.option("-nm", "--nomount", is_flag=True, help="if set will delete the docker container if it already exists")
def container_shell(name="3bot", delete=False, nomount=False):
    """
    open a  shell to the container for 3bot
    :param name: name of container if not the default
    :return:
    """
    _container_shell(name=name, delete=delete, nomount=nomount)


def _container_shell(name="3bot", delete=False, nomount=False):
    """
    open a  shell to the container for 3bot
    :param name: name of container if not the default
    :return:
    """
    mount = not nomount
    docker = container_get(name=name, delete=delete, mount=mount, install=False, jumpscale=True)
    msg = """
    WELCOME TO YOUR INSTALLED LOCAL KOSMOS ENVIRONMENT (THREEBOT)
    
    some tips to get started

    - kosmos  : to get shell into the environment    
    - tmux a  : to see the parallel processes running (ctrl b 1 to e.g. go to panel 1)
    - htop    : to see which processes are taking how much resource
    - to to your local machine and use browser to go to: http://localhost:7020/ will show webinterface
    
    """
    docker.sshshell("source /sandbox/env.sh;cd /sandbox/;clear;echo '%s';bash" % IT.Tools.text_replace(msg))
    # docker.sshshell()


@click.command()
@click.option("-n", "--name", default="3bot", help="name of container")
@click.option("-t", "--test", is_flag=True, help="use j.shell inside wireguard to play around, obj to look at is 'wg'")
@click.option("-d", "--disconnect", is_flag=True, help="disconnect")
def wireguard(name=None, test=False, disconnect=False):
    """
    jsx wireguard
    enable wireguard, can be on host or server
    :return:
    """
    docker = container_get(name=name)
    wg = docker.wireguard
    if disconnect:
        wg.disconnect()
    elif test:
        print(wg)
        IT.Tools.shell()
    else:
        wg.reset()
        print(wg)
        wg.server_start()
        wg.connect()


@click.command()
@click.option("-t", "--test", is_flag=True, help="use j.shell inside wireguard to play around, obj to look at is 'wg'")
@click.option("-d", "--disconnect", is_flag=True, help="disconnect")
def connect(test=False, disconnect=False):
    """
    only for core developers and engineers of threefold, will connect to some core
    infrastructure for helping us to communicate
    :return:
    """
    myid = IT.MyEnv.registry.myid
    addr = IT.MyEnv.registry.addr[0]
    wg = IT.WireGuardServer(addr=addr, myid=myid)
    if disconnect:
        wg.disconnect()
    elif test:
        print(wg)
        IT.Tools.shell()
    else:
        wg.reset()
        print(wg)
        wg.server_start()
        wg.connect()


@click.command()
@click.option("-c", "--count", default=1, help="nr of containers")
@click.option("-n", "--net", default="172.0.0.0/16", help="network range for docker")
@click.option(
    "-d", "--delete", is_flag=True, help="if set will delete the test container for threebot if it already exists"
)
@click.option("-w", "--web", is_flag=True, help="if set will install the wikis")
@click.option("-p", "--pull", is_flag=True, help="pull the docker image")
def threebot(delete=False, count=1, net="172.0.0.0/16", web=False, pull=False):
    """

    jsx threebot -d

    :param delete:  delete the containers you want to use in this test
    :param name:    base name, if more than 1 container then will name+nr e.g. 3bot2  the first one always is 3bot
    :param count:   nr of containers to create in test, they will all be able to talk to each other
    :param net:     the network to use for the containers
    :param web:     if the wiki needs to be started
    :return:
    """

    name = "3bot"
    if pull:
        cmd = "docker pull threefoldtech/3bot2"
        IT.Tools.execute(cmd, interactive=True)

    def docker_jumpscale_get(name=name, delete=True):
        docker = e._DF.container_get(name=name, delete=delete)
        if docker.config.done_get("threebot") is False:
            # means we have not installed jumpscale yet
            docker.install()
            docker.install_jumpscale(threebot=True)
            # now we can access it over 172.0.0.x normally
            docker.config.done_set("threebot")
            docker.config.save()
        return docker

    def configure():
        """
        will be executed in each container
        :return:
        """
        # j.clients.threebot.explorer_addr_set("{explorer_addr}")
        docker_name = "{docker_name}"
        j.tools.threebot.init_my_threebot(
            name="{docker_name}.3bot", email="{docker_name}@threefold.io", interactive=False
        )
        j.clients.threebot.explorer.reload()  # make sure we have the actors loaded
        # lets low level talk to the phonebook actor
        # print(j.clients.threebot.explorer.actors_all.phonebook.get(name="{docker_name}.3bot"))
        cl = j.clients.threebot.client_get("{docker_name}.3bot")

        r1 = j.tools.threebot.explorer.threebot_record_get(name="{docker_name}.3bot")
        print(r1)
        r2 = j.tools.threebot.explorer.threebot_record_get(tid=cl.tid)
        assert r2 == r1

    def test():
        docker_name = "{docker_name}"
        nr_containers = int("{count}")

        print("RUNNING TESTS FROM {docker_name}")

        clients = list()

        clients.append(j.clients.threebot.explorer)
        clients += [j.clients.threebot.client_get("3bot{0}.3bot".format(i + 1)) for i in range(1, nr_containers - 1)]
        for client in clients:
            print("connected to ", client.name, "on", client.host)
            print("---identity---", client.name, "\n", client.actors_all.identity.threebot_name())

        j.clients.threebot.explorer.reload()
        j.clients.threebot.explorer.actors_all.package_manager.package_start(
            "tfgrid.directory"
        )  # TODO: Fix. we shouldn't have to load here
        nodes = j.clients.threebot.explorer.actors_all.nodes.list()

        print("EXPLORER NODES:")
        print(nodes)

    explorer_addr = None
    for i in range(count):
        if i > 0:
            name1 = name + str(i + 1)
        else:
            name1 = name
        docker = docker_jumpscale_get(name=name1, delete=delete)
        # if i == 0:
        #     # the explorer 3bot
        #     # explorer_addr = docker.config.ipaddr
        #     # TODO: why did we do influxdb?
        #     # docker.sshexec("apt-get install influxdb")
        #     # docker.jsxexec("sc = j.servers.startupcmd.get('influxd', cmd_start='influxd'); sc.start()")
        #     # time.sleep(2)
        #     # docker.jsxexec("j.clients.influxdb.get('default', database='capacity').create_database('capacity')")
        #     # NO LONGER USED BECAUSE EXPLORER IS CENTRAL
        #     # docker.jsxexec(configure, explorer_addr=explorer_addr, docker_name=docker.name)
        #     # docker.sshexec(
        #     #     "source /sandbox/env.sh; python3 /sandbox/code/github/threefoldtech/jumpscaleX_threebot/scripts/explorer.py stress-explorer --count 10"
        #     # )
        # else:
        #     raise RuntimeError("not implemented")
        #     start_cmd = "j.servers.threebot.start(background=True)"
        #     docker.jsxexec(start_cmd)
        #     docker.jsxexec(configure, explorer_addr=explorer_addr, docker_name=docker.name)
        # TODO: to check test works
        # if i == count - 1:
        #     # on last docker do the test
        #     docker.jsxexec(test, docker_name=docker.name, count=count)

    try:
        import webbrowser

        webbrowser.open_new_tab("http://localhost:7020")
    except:
        pass

    _container_shell()


@click.command(name="modules-install")
# @click.option("--configdir", default=None, help="default {DIR_BASE}/cfg if it exists otherwise ~{DIR_BASE}/cfg")
@click.option("--url", default="3bot", help="git url e.g. https://github.com/myfreeflow/kosmos")
def modules_install(url=None):
    """
    install jumpscale module in local system
    :return:
    """
    from Jumpscale import j

    path = j.clients.git.getContentPathFromURLorPath(url)
    _generate(path=path)


@click.command()
def generate():
    _generate()


@click.command()
def check():
    from Jumpscale import j

    j.application.interactive = True
    j.application.check()


def _generate(path=None):
    j = jumpscale_get(die=True)
    j.application.generate(path)


@click.command(name="package-new", help="scaffold a new package tree structure")
@click.option("--name", help="new package name")
@click.option("--dest", default="", help="new package destination (current dir if not specified)")
def package_new(name, dest=None):
    j = jumpscale_get(die=True)
    if not dest:
        dest = j.sal.fs.getcwd()
    capitalized_name = name.capitalize()
    dirs = ["wiki", "models", "actors", "chatflows"]
    package_toml_path = j.sal.fs.joinPaths(dest, f"{name}/package.toml")
    package_py_path = j.sal.fs.joinPaths(dest, f"{name}/package.py")

    for d in dirs:
        j.sal.fs.createDir(j.sal.fs.joinPaths(dest, name, d))

    package_toml_content = f"""
[source]
name = "{name}"
description = "mypackage"
threebot = "mybot"
version = "1.0.0"


[[bcdbs]]
namespace = "mybot"
type = "zdb"
instance = "default"
    """

    with open(package_toml_path, "w") as f:
        f.write(package_toml_content)

    package_py_content = f"""
from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    pass

    """

    with open(package_py_path, "w") as f:
        f.write(package_py_content)

    actor_py_path = j.sal.fs.joinPaths(dest, name, "actors", f"{name}.py")
    actor_py_content = f"""
from Jumpscale import j


class {name}(j.baseclasses.threebot_actor):
    pass
    """
    with open(actor_py_path, "w") as f:
        f.write(actor_py_content)

    chat_py_path = j.sal.fs.joinPaths(dest, name, "chatflows", f"{name}.py")
    chat_py_content = f"""
from Jumpscale import j
import gevent


def chat(bot):

    # form = bot.new_form()
    # food = form.string_ask("What do you need to eat?")
    # amount = form.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    # sides = form.multi_choice("Choose your side dishes: ", ["rice", "fries", "saute", "mashed potato"])
    # drink = form.single_choice("Choose your Drink: ", ["tea", "coffee", "lemon"])
    # form.ask()

    # bot.md_show(res)
    # bot.redirect("https://threefold.me")
    pass

    """
    with open(chat_py_path, "w") as f:
        f.write(chat_py_content)


if __name__ == "__main__":

    cli.add_command(configure)
    cli.add_command(check)
    cli.add_command(install)
    cli.add_command(kosmos)
    cli.add_command(generate)
    cli.add_command(wireguard)
    cli.add_command(modules_install, "modules-install")
    cli.add_command(wiki_load, "wiki-load")
    cli.add_command(wiki_reload)
    cli.add_command(package_new, "package-new")
    cli.add_command(jumpscale_code_get, "jumpscale-code-get")
    cli.add_command(connect)

    # DO NOT DO THIS IN ANY OTHER WAY !!!
    if not e._DF.indocker():
        cli.add_command(container_kosmos, "container-kosmos")
        cli.add_command(container_install, "container-install")
        cli.add_command(container_stop, "container-stop")
        cli.add_command(container_start, "container-start")
        cli.add_command(container_delete, "container-delete")
        cli.add_command(containers_reset, "containers-reset")
        cli.add_command(container_export, "container-export")
        cli.add_command(container_import, "container-import")
        cli.add_command(container_shell, "container-shell")
        cli.add_command(container_save, "container-save")
        cli.add_command(basebuilder, "basebuilder")
        cli.add_command(threebotbuilder, "threebotbuilder")
        cli.add_command(threebot_flist, "threebot-flist")
        cli.add_command(containers)
        cli.add_command(threebot, "threebot")

    cli()
