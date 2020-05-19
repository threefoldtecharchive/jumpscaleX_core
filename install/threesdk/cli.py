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
    installer,
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
            f"Your SDK version is not up-to-date. Newest release is {dic['latest_release']}\nPlease visit: {dic['latest_release_url']}\nOr run '3sdk --update'"
        )


def update():
    """
    """
    from threesdk import container
    from threesdk.InstallTools import JumpscaleInstaller, MyEnv, Tools, DockerFactory

    if not Tools.is_latest_release():
        installer = JumpscaleInstaller()
        containers_names = DockerFactory.containers()
        host_mount = False
        # pull all repos in containers
        for item in containers_names:
            name = item.name
            print("Updating repositories in container ", name, "...")
            container._containers.assert_container(name)
            c = DockerFactory.container_get(name=name)
            if not c.mount_code_exists:
                container_executor = c.executor
                installer.repos_get(pull=True, executor=container_executor)
            else:
                host_mount = True
        if host_mount:
            installer.repos_get(pull=True)

        import requests

        # Update binary for host
        print("Downloading 3sdk binary...")
        latest_release = Tools.get_latest_release()
        with requests.get(latest_release["download_link"], allow_redirects=True, stream=True) as r:
            if MyEnv.platform_is_linux or MyEnv.platform_is_osx:
                local_filename = "/tmp/3sdk"
                with open(local_filename, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
                f.close()
                print("Download done, installing now ..")
                os.chmod(local_filename, 0o775)
                # _, bin_path, _ = Tools.execute(f"which 3sdk")
                bin_path = shutil.which("3sdk")
                # save backup
                shutil.copy(bin_path, "/tmp/3sdk.bk")
                # replace
                try:
                    shutil.move("/tmp/3sdk", bin_path)
                    print(bin_path)
                    print("Congratulations, Now your 3sdk is up-to-date!")
                except:
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
    else:
        print(f"3sdk version is up-to-date")


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
    parser.add_argument("--update", default=False, action="store_true")
    parser.add_argument("-v", "--version", default=False, action="store_true")

    options, extra = parser.parse_known_args()
    base_check(options.expert)
    if options.update:
        update()
        sys.exit(0)
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
