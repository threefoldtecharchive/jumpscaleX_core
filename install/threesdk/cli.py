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
    # from InstallTools import get_newest_version
    dic = _sdk.InstallTools.Tools.get_newest_version()
    # campare with __version__
    if not dic["up_to_date"]:
        print(
            f"Your SDK version is not up-to-date. Newest release is {dic['last_release']}\nPlease visit: {dic['last_release_url']}"
        )


def update():
    """
    """
    from threesdk import container

    containers_names = container._containers.IT.DockerFactory.containers()
    for item in containers_names:
        name = item.name
        print("Updating repositories in container: ", name)
        container._containers.assert_container(name)
        c = container._containers.get(name=name, explorer="none")
        container_executor = c.executor
        from threesdk.InstallTools import JumpscaleInstaller

        JumpscaleInstaller.repos_get(JumpscaleInstaller, pull=True, executor=container_executor)


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

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--expert", default=False, action="store_true")
    parser.add_argument("-v", "--version", default=False, action="store_true")

    sub_parser = argparse.ArgumentParser(add_help=False)
    subparsers = sub_parser.add_subparsers()
    # subcommand update
    parser_update = subparsers.add_parser("update", parents=[parser])

    options, extra = parser.parse_known_args()
    base_check(options.expert)
    if options.version:
        version()
        sys.exit(0)

    args.args.expert = options.expert

    if "update" in extra:
        update()
        extra.remove("update")
    if extra:
        line = rewriteline(extra, globals(), locals())
        exec(line, globals(), locals())
    else:
        shell(locals_=locals(), globals_=globals(), expert=options.expert)


if __name__ == "__main__":
    # the shell should only show d... j...  (no capitals at start of sentence)
    # logger needs to be redirected properly
    main()
