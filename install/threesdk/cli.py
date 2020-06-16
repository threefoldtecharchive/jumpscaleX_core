#!/usr/bin/env python3
import sys
import os
import shutil


import jedi
import threesdk as _sdk
import cgi

from ptpython.repl import embed

from functools import partial
from threesdk.shell import ptconfig, rewriteline
from threesdk import (
    container,
    threebot,
    builder,
    simulator,
    install,
    args,
    core,
    _get_doc_line,
)  # pylint: disable=F401

from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import HTML


IT = core.core.IT
# for auto-completion data
# also, jedi and parso hooks need to be available
# for autoc-completion to work with pyinstaller build
jedi.preload_module("_sdk")


def get_doc(root_module, level=0, size=4):
    """get a formatted docstring from a module
    this will loop over __all__self.

    :param root_module: root module
    :type root_module: module
    :param level: spacing level, defaults to 0
    :type level: int, optional
    :param level: spacing size, defaults to 4
    :type level: int, optional
    :return: docstring
    :rtype: str
    """
    import inspect

    doc = ""

    if hasattr(root_module, "__all__"):
        members = [(name, getattr(root_module, name)) for name in root_module.__all__]
    else:
        members = inspect.getmembers(root_module)
    for name, obj in members:
        if name.startswith("_"):
            continue
        if name[0].lower() != name[0]:
            continue

        is_module = inspect.ismodule(obj)
        if is_module and level != 0:
            continue

        spaces = " " * level

        if is_module:
            doc += f"{spaces}<ansibrightblue>{name}</ansibrightblue>"
        elif getattr(obj, "__property__", False):
            doc += f"{spaces}<ansicyan>{name}</ansicyan>"
        else:
            doc += f"{spaces}<ansigreen>{name}</ansigreen>"

        if obj.__doc__:
            try:
                # only get first line of member docstring
                first_line = _get_doc_line(obj.__doc__)
                doc += cgi.html.escape(f": {first_line}")
            except IndexError:
                pass

        doc = f"{doc}\n"

        if is_module:
            doc += get_doc(obj, level=level + size)

    return doc


def info():
    """
    show commands available in 3sdk
    """
    print_formatted_text(HTML(get_doc(_sdk)))


def exit():
    """
    Exit shell
    """
    sys.exit(0)


def version():
    """
    Print version number
    """
    print(f"3sdk {_sdk.__version__}")
    # campare with __version__
    if not _sdk.InstallTools.Tools.is_latest_release():
        dic = _sdk.InstallTools.Tools.get_latest_release()
        print(
            f"Your SDK version is not up-to-date. Newest release is {dic['latest_release']}\nPlease visit: {dic['latest_release_url']}\nOr run '3sdk update'"
        )


def update(branch="master"):
    """
    Update 3sdk binary in place and update containers to latest version, you threebot server will be restarted during this process
    """
    from threesdk.InstallTools import JumpscaleInstaller, MyEnv, Tools, DockerFactory

    import requests
    binuptodate = Tools.is_latest_release()

    installer = JumpscaleInstaller()
    containers_names = DockerFactory.containers()
    host_mount = False
    # pull all repos in containers
    for item in containers_names:
        name = item.name
        container._containers.assert_container(name)
        c = DockerFactory.container_get(name=name)
        if c.mount_code_exists:
            host_mount = True
        else:
            print("Updating repos in container ", name, "...")
            container_executor = c.executor
            installer.repos_get(pull=True, executor=container_executor, branch=branch)

    if host_mount:
        print("Updating repos on host...")
        installer.repos_get(pull=True, branch=branch)

    # restart containers
    for item in containers_names:
        name = item.name
        c = DockerFactory.container_get(name=name)
        if name == "simulator":
            simulator.restart(container=True, browser_open=False)
        elif name == "3bot":
            threebot.restart(container=True, browser_open=False)
        else:
            rc, out, err = c.execute(
                "pgrep -f /sandbox/var/cmds/threebot_default.py", interactive=False, die=False, showout=True,
            )

            container.stop(name=name)
            if rc > 0:
                container.start(name=name, server=False)
            else:
                print(f"container {name} is running 3bot server")
                container.start(name=name, server=True, browser_open=False)
    if not binuptodate:
        # Update binary for host
        print("Downloading 3sdk binary...")
        latest_release = Tools.get_latest_release()
        with requests.get(latest_release["download_link"], allow_redirects=True, stream=True) as r:
            if MyEnv.platform_is_linux or MyEnv.platform_is_osx:
                local_filename = "/tmp/3sdk"
                with open(local_filename, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
                r.close()
                print("Download done, installing now ..")
                os.chmod(local_filename, 0o775)
                bin_path = sys.argv[0]
                # save backup
                shutil.copy(bin_path, "/tmp/3sdk.bk")
                # replace
                try:
                    shutil.move("/tmp/3sdk", bin_path)
                    print(bin_path)
                    print("Congratulations, Now your 3sdk is up-to-date!")
                except Exception:
                    shutil.copy("/tmp/3sdk.bk", bin_path)
                    print(f"Failed to update binary, Can not replace binary in {bin_path}")
            elif MyEnv.platform_is_windows:
                update_path = f"{os.environ['USERPROFILE']}\\3sdk\\3sdk_update.exe"
                print("Download done, installing now ..")
                with open(update_path, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
                f.close()
                Tools.execute(f'explorer "{update_path}"', interactive=True)
            else:
                raise Tools.exceptions.Base("platform not supported, only linux, osx and windows.")


def shell(loc=False, exit=False, locals_=None, globals_=None, expert=False):
    import inspect

    if not expert:
        _sdk.__all__.remove("builder")
        _sdk.__all__.remove("installer")
        _sdk.__all__.remove("install")
        _sdk.__all__.remove("container")

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    f = calframe[1]
    if loc:
        print("\n*** file: %s" % f.filename)
        print("*** function: %s [linenr:%s]\n" % (f.function, f.lineno))

    print("Welcome to sdk shell, for help, type info, to exit type exit")

    history_filename = "%s/.jsx_sdk_history" % IT.MyEnv.config["DIR_HOME"]
    if not IT.Tools.exists(history_filename):
        IT.Tools.file_write(history_filename, "")

    myptconfig = partial(ptconfig, expert=expert)
    result = embed(globals_, locals_, configure=myptconfig, history_filename=history_filename)
    if exit:
        sys.exit(result)
    return result


def base_check(expert):
    requiretools = ["docker"]
    if expert:
        requiretools.append("git")
    missingtools = []
    for tool in requiretools:
        if not shutil.which(tool):
            missingtools.append(tool)
    if os.name == "nt":
        link = "https://sdk.threefold.io/#/3sdk_windows?id=requirements"
    else:
        link = "https://sdk.threefold.io/#/3sdk_install?id=requirements"
    if missingtools:
        print(f"Some required tools '{', '.join(missingtools)}' are missing on your system  see {link} for more info.")
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--expert", default=False, action="store_true")
    parser.add_argument("-v", "--version", default=False, action="store_true")
    parser.add_argument("update", default=False, action="store_true", help="Update 3sdk and 3bot/simulator")

    options, extra = parser.parse_known_args()
    if "update" in extra and extra.index("update") == 0:
        update()
        sys.exit(0)

    base_check(options.expert)
    if options.version:
        version()
        sys.exit(0)

    args.args.expert = options.expert
    if extra:
        line = rewriteline(extra, globals(), locals())
        exec(line, globals(), locals())
    else:
        shell(locals_=locals(), globals_=globals(), expert=options.expert)


if __name__ == "__main__":
    # the shell should only show d... j...  (no capitals at start of sentence)
    # logger needs to be redirected properly
    main()
