#!/usr/bin/env python3
import click
import os
import requests
from urllib.request import urlopen
from importlib import util

DEFAULT_BRANCH = "development"
os.environ["LC_ALL"] = "en_US.UTF-8"


def load_install_tools(branch=None, reset=False):
    # get current install.py directory

    path = "/sandbox/code/github/threefoldtech/jumpscaleX_core/install/threesdk/InstallTools.py"
    if not os.path.exists(path):
        path = os.path.expanduser("~/sandbox/code/github/threefoldtech/jumpscaleX_core/install/threesdk/InstallTools.py")

    if not branch:
        branch = DEFAULT_BRANCH
    # first check on code tools
    if not os.path.exists(path):
        rootdir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(rootdir, "InstallTools.py")
        # now check on path next to jsx
        if not os.path.exists(path) or reset:  # or path.find("/code/") == -1:
            url = "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/threesdk/InstallTools.py" % branch

            # fallback to default branch if installation is being done for another branch that doesn't exist in core
            if branch != DEFAULT_BRANCH and requests.get(url).status_code == 404:
                url = (
                    "https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/%s/install/threesdk/InstallTools.py"
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


def jumpscale_get(die=True):
    # jumpscale need to be available otherwise cannot do
    try:
        from Jumpscale import j
    except Exception:
        if die:
            raise RuntimeError("ERROR: cannot use jumpscale yet, has not been installed")
        return None
    return j


@click.group()
def cli():
    pass


# INSTALL OF JUMPSCALE IN CONTAINER ENVIRONMENT
@click.command()
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
@click.option("--threebot", is_flag=True, help="install required components for threebot")
@click.option("-s", "--no-interactive", is_flag=True, help="default is interactive, -s = silent")
@click.option("-i", "--identity", default=None, help="Identity to be used for the 3bot functionality")
@click.option("--reset", is_flag=True, help="Delete BCDB, dangerous !")
@click.option("--email", help="email address to be used")
@click.option("--words", help="words of private key retrieved from 3bot connect app")
def install(
    reinstall=False, pull=False, no_interactive=False, threebot=False, identity=None, reset=None, email=None, words=None
):
    """
    install jumpscale in the local system (only supported for Ubuntu 18.04+ and mac OSX, use container install method otherwise.
    if interactive is True then will ask questions, otherwise will go for the defaults or configured arguments

    if you want to configure other arguments use 'jsx configure ... '


    """

    IT.MyEnv.interactive = not no_interactive
    if reinstall:
        # remove the state
        IT.MyEnv.state_reset()
        force = True
    else:
        force = False

    installer = IT.JumpscaleInstaller()
    installer.install(
        sandboxed=False,
        force=force,
        gitpull=pull,
        threebot=threebot,
        identity=identity,
        reset=reset,
        email=email,
        words=words,
    )
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
def getcode(branch=None, pull=False, reset=False):
    """
    checkout the code onto your local filesystem
    """
    # IT.MyEnv.interactive = True

    if not branch:
        branch = IT.DEFAULT_BRANCH
    installer = IT.JumpscaleInstaller()
    installer.repos_get(pull=pull, reset=reset)
    # IT.Tools.shell()


#
# @click.command(name="threebot-flist")
# @click.option("-i", "--app_id", default=None, help="application id of it's your online")
# @click.option("-s", "--secret", default=None, help="secret of it's your it's your online account")
# def threebot_flist(app_id=None, secret=None):
#     """
#     create flist of 3bot docker image
#     ex: jsx threebot-flist -i APP_ID -s SECRET -u USER_NAME
#     """
#     if not app_id and not secret:
#         raise RuntimeError("should add it's your online creds")
#
#     url = urllib.parse.urljoin("https://itsyou.online/api", "/v1/oauth/access_token")
#     params = {
#         "grant_type": "client_credentials",
#         "client_id": app_id,
#         "client_secret": secret,
#         "response_type": "id_token",
#         "scope": "",
#         "validity": None,
#     }
#
#     resp = requests.post(url, params=params)
#     resp.raise_for_status()
#     jwt = resp.content.decode("utf8")
#
#     params = {"image": "threefoldtech/3bot2:corex"}
#     url = "https://hub.grid.tf/api/flist/me/docker"
#     headers = {"Authorization": "Bearer %s" % jwt}
#     requests.post(url, headers=headers, data=params)
#     print("uploaded 3bot flist")
#
#


@click.command()
@click.argument("secret")
def secret_set(secret=None):
    if not secret:
        secret = IT.Tools.ask_password("please provide passphrase")
    IT.RedisTools._core_get()
    IT.MyEnv.secret_set(secret=secret, secret_expiration_hours=48)


# @click.command(name="modules-install")
# # @click.option("--configdir", default=None, help="default {DIR_BASE}/cfg if it exists otherwise ~{DIR_BASE}/cfg")
# @click.option("--url", default="3bot", help="git url e.g. https://github.com/myfreeflow/kosmos")
# def modules_install(url=None):
#     """
#     install jumpscale module in local system
#     :return:
#     """
#     from Jumpscale import j
#
#     path = j.clients.git.getContentPathFromURLorPath(url)
#     _generate(path=path)


@click.command()
def generate():
    j = jumpscale_get(die=True)
    j.application.generate()


@click.command()
def check():
    from Jumpscale import j

    j.application.interactive = True
    j.application.check()


#
# @click.command(name="package-new", help="scaffold a new package tree structure")
# @click.option("--name", help="new package name")
# @click.option("--dest", default="", help="new package destination (current dir if not specified)")
# def package_new(name, dest=None):
#     j = jumpscale_get(die=True)
#     if not dest:
#         dest = j.sal.fs.getcwd()
#     capitalized_name = name.capitalize()
#     dirs = ["wiki", "models", "actors", "chatflows"]
#     package_toml_path = j.sal.fs.joinPaths(dest, f"{name}/package.toml")
#     package_py_path = j.sal.fs.joinPaths(dest, f"{name}/package.py")
#
#     for d in dirs:
#         j.sal.fs.createDir(j.sal.fs.joinPaths(dest, name, d))
#
#     package_toml_content = f"""
# [source]
# name = "{name}"
# description = "mypackage"
# threebot = "mybot"
# version = "1.0.0"
#
#
# [[bcdbs]]
# name = "mybot_{name}"
# namespace = "mybot_{name}"
# type = "zdb"
# instance = "default"
#     """
#
#     with open(package_toml_path, "w") as f:
#         f.write(package_toml_content)
#
#     package_py_content = f"""
# from Jumpscale import j
#
#
# class Package(j.baseclasses.threebot_package):
#     pass
#
#     """
#
#     with open(package_py_path, "w") as f:
#         f.write(package_py_content)
#
#     actor_py_path = j.sal.fs.joinPaths(dest, name, "actors", f"{name}.py")
#     actor_py_content = f"""
# from Jumpscale import j
#
#
# class {name}(j.baseclasses.threebot_actor):
#     pass
#     """
#     with open(actor_py_path, "w") as f:
#         f.write(actor_py_content)
#
#     chat_py_path = j.sal.fs.joinPaths(dest, name, "chatflows", f"{name}.py")
#     chat_py_content = f"""
# from Jumpscale import j
# import gevent
#
#
# def chat(bot):
#
#     # form = bot.new_form()
#     # food = form.string_ask("What do you need to eat?")
#     # amount = form.int_ask("Enter the amount you need to eat from %s in grams:" % food)
#     # sides = form.multi_choice("Choose your side dishes: ", ["rice", "fries", "saute", "mashed potato"])
#     # drink = form.single_choice("Choose your Drink: ", ["tea", "coffee", "lemon"])
#     # form.ask()
#
#     # bot.md_show(res)
#     # bot.redirect("https://threefold.me")
#     pass
#
#     """
#     with open(chat_py_path, "w") as f:
#         f.write(chat_py_content)


if __name__ == "__main__":

    # cli.add_command(ssh)
    cli.add_command(check)
    cli.add_command(install)
    # cli.add_command(kosmos)
    cli.add_command(generate)
    # cli.add_command(wireguard)
    # cli.add_command(modules_install, "modules-install")
    # cli.add_command(wiki_load, "wiki-load")
    # cli.add_command(wiki_reload)
    # cli.add_command(package_new, "package-new")
    cli.add_command(getcode)
    # cli.add_command(connect)
    # cli.add_command(configure)
    cli.add_command(secret_set, "secret")
    cli()
