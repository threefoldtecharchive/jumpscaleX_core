from Jumpscale import j

import sys
import os
import inspect

# import os.path
from functools import wraps
import re

joinPaths = os.path.join
exists = os.path.exists
getcwd = os.getcwd


def pathShorten(path):
    """
    """
    cleanedPath = os.path.normpath(path)
    # if j.core.platformtype.myplatform.platform_is_windows and exists(cleanedPath):
    #     # Only execute on existing paths, otherwise an error will be raised
    #     import win32api
    #     cleanedPath = win32api.GetShortPathName(cleanedPath)
    #     # Re-add '\' if original path had one
    #     sep = os.path.sep
    #     if path and path[-1] == sep and cleanedPath[-1] != sep:
    #         cleanedPath = "%s%s" % (cleanedPath, sep)
    return cleanedPath


def pathClean(path):
    """
    goal is to get a equal representation in / & \ in relation to os.sep
    """
    path = path.replace("/", os.sep)
    path = path.replace("//", os.sep)
    path = path.replace("\\", os.sep)
    path = path.replace("\\\\", os.sep)
    # path=pathNormalize(path)
    path = path.strip()
    return path


def pathDirClean(path):
    path = path + os.sep
    return pathClean(path)


def dirEqual(path1, path2):
    return pathDirClean(path1) == pathDirClean(path2)


def pathNormalize(path):
    """
    paths are made absolute & made sure they are in line with os.sep
    @param path: path to normalize
    """
    if path == "":
        return getcwd()
    path = pathClean(path)
    if len(path) > 0 and path[0] != os.sep:
        if path[0] == "~":
            path = joinPaths(os.getenv("HOME"), path[2:])
        else:
            path = joinPaths(getcwd(), path)
    path = pathShorten(path)
    return path


def cleanupString(string, replacewith="_", regex="([^A-Za-z0-9])"):
    """Remove all non-numeric or alphanumeric characters"""
    # Please don't use the logging system here. The logging system
    # needs this method, using the logging system here would
    # introduce a circular dependency. Be careful not to call other
    # functions that use the logging system.
    return re.sub(regex, replacewith, string)


def path_check(**arguments):
    """ Decorator to check if specified path arguments pass the
        specified validators.
        The following validations are supported:
        - "required": Means that the path argument value must not be None
                       or empty string
        - "exists": Means that the path argument value must be an
                       existing directory
        - "replace": Means we replace the path or filename using j.core.tools.text_replace

        - "file": Means that the path argument value must be an
                       existing file or a link to a file
        - "pureFile": Means that the path argument value must be an existing
                       file
        - "dir": Means that the path argument value must be an
                       existing directory or a link to a directory
        - "pureDir": Means that the path argument value must be an
                       existing directory

        - "multiple": Means will check if multiple arguments (comma separated or list), if yes execute the method multiple times

        When no validations are added, the value of the path argument will still
        be expanded with the current home directory if the path starts with ~

        E.g.
        @path_check(sourceDir={"required","exists"}, destDir={"required"})
        def copyDir(sourceDir, destDir):
            pass
    """
    for argument, validators in arguments.items():
        if not isinstance(validators, set):
            raise j.exceptions.Value("Expected tuple of validators for argument %s" % argument)
        for validator in validators:
            if validator not in {"required", "exists", "file", "dir", "pureFile", "pureDir", "replace", "multiple"}:
                raise j.exceptions.Value("Unsupported validator '%s' for argument %s" % (validator, argument))

    def decorator(func):
        signature = inspect.signature(func)
        for argument in arguments:
            if signature.parameters.get(argument) is None:
                raise j.exceptions.Value(
                    "Argument %s not found in function declaration of %s" % (argument, func.__name__)
                )

        @wraps(func)
        def wrapper(*args, **kwargs):
            def jslocation():
                return "%s." % args[0].__jslocation__ if hasattr(args[0], "__jslocation__") else ""

            args = list(args)
            position = 0
            for parameter in signature.parameters.values():
                if parameter.name in arguments:
                    value = args[position] if position < len(args) else kwargs[parameter.name]
                    value = j.core.tools.text_replace(value)  # replace the default dir arguments
                    if value and value.startswith("~%s" % os.sep):
                        if "HOME" in os.environ:
                            value = os.path.expanduser(value)
                        else:
                            value = "%s%s" % (j.dirs.HOMEDIR, value[1:])
                        if position < len(args):
                            args[position] = value
                        else:
                            kwargs[parameter.name] = value

                    validators = arguments[parameter.name]
                    if (
                        value
                        and validators.intersection({"exists", "file", "dir", "pureFile", "pureDir"})
                        and not os.path.exists(value)
                    ):
                        msg = "Argument %s in %s%s expects an existing path value! %s does not exist." % (
                            parameter.name,
                            jslocation(),
                            func.__name__,
                            value,
                        )
                        raise j.exceptions.Value(msg)
                    if "required" in validators and (value is None or value.strip() == ""):
                        raise j.exceptions.Value(
                            "Argument %s in %s%s should not be None or empty string!"
                            % (parameter.name, jslocation(), func.__name__)
                        )

                    if "required" in validators:
                        # NORMALIZE THE PATH
                        value = pathNormalize(value)
                        if position < len(args):
                            args[position] = value
                        else:
                            kwargs[parameter.name] = value

                    if "replace" in validators:
                        # replace THE PATH
                        value = j.core.tools.text_replace(value)
                        if position < len(args):
                            args[position] = value
                        else:
                            kwargs[parameter.name] = value

                    if value and validators.intersection({"file", "pureFile"}) and not os.path.isfile(value):
                        raise j.exceptions.Value(
                            "Argument %s in %s%s expects a file path! %s is not a file."
                            % (parameter.name, jslocation(), func.__name__, value)
                        )
                    if value and "pureFile" in validators and os.path.islink(value):
                        raise j.exceptions.Value(
                            "Argument %s in %s%s expects a file path! %s is not a file but a link."
                            % (parameter.name, jslocation(), func.__name__, value)
                        )
                    if value and validators.intersection({"dir", "pureDir"}) and not os.path.isdir(value):
                        raise j.exceptions.Value(
                            "Argument %s in %s%s expects a directory path! %s is not a directory."
                            % (parameter.name, jslocation(), func.__name__, value)
                        )
                    if value and "pureDir" in validators and os.path.islink(value):
                        raise j.exceptions.Value(
                            "Argument %s in %s%s expects a directory path! %s is not a directory but a link."
                            % (parameter.name, jslocation(), func.__name__, value)
                        )

                    if "multiple" in validators:
                        if j.data.types.list.check(value) or "," in value:
                            raise j.exceptions.Base(
                                "need to implement support for multiple times execution, is more difficult"
                            )
                            # replace THE PATH
                            value = j.core.tools.text_replace(value)
                            if position < len(args):
                                args[position] = value
                            else:
                                kwargs[parameter.name] = value

                position += 1
            return func(*args, **kwargs)

        return wrapper

    return decorator
