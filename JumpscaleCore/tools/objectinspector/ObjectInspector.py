import os
import inspect
import types
from collections import OrderedDict
import json
from Jumpscale import j

# api codes
# 4 function with params
# 7 ???
# 8 property
JSBASE = j.baseclasses.object


class Arg(j.baseclasses.object):
    """
        Wrapper for argument
    """

    def __init__(self, name, defaultvalue):
        self.name = name
        self.defaultvalue = defaultvalue
        JSBASE.__init__(self)

    def __str__(self):
        out = ""
        if self.defaultvalue is not None:
            out += "- %s = %s\n" % (self.name, self.defaultvalue)
        else:
            out += "- %s\n" % (self.name)
        return out

    def __repr__(self):
        return self.__str__()


def attrib(name, type, doc=None, objectpath=None, filepath=None, extra=None):
    """
    Helper function for codecompletion tree.
    """
    return (name, type, doc, objectpath, filepath, extra)


class MethodDoc(j.baseclasses.object):
    """
    Method documentation
    """

    def __init__(self, method, name, classdoc):
        self.classdoc = classdoc
        self.params = []
        JSBASE.__init__(self)

        inspected = inspect.getargspec(method)
        if inspected.defaults is not None:
            counter = len(inspected.defaults) - len(inspected.args)
        else:
            counter = -99999

        for param in inspected.args:
            if inspected.defaults is not None and counter > -1:
                defval = inspected.defaults[counter]
                if j.data.types.string.check(defval):
                    defval = "'%s'" % defval
            else:
                defval = None
            counter += 1
            if param != "self":
                self.params.append(Arg(param, defval))

        if inspected.varargs is not None:
            self.params.append(Arg("*%s" % inspected.varargs, None))

        if inspected.keywords is not None:
            self.params.append(Arg("**%s" % inspected.keywords, None))

        self.comments = inspect.getdoc(method)
        if self.comments is None:
            self.comments = ""
        self.comments = j.core.text.strip(self.comments)
        self.comments = j.core.text.wrap(self.comments, 90)

        self.linenr = inspect.getsourcelines(method)[1]
        self.name = name

        # self.methodline=inspect.getsourcelines(method)[0][0].strip().replace("self, ","").replace("self,","").replace("self","").replace(":","")

    def __str__(self):
        """
        Markdown representation of the method and its arguments
        """
        out = ""
        param_s = ""
        if len(self.params) > 0:
            param_s = ", ".join(
                [str(arg.name) + "=" + str(arg.defaultvalue) if arg.defaultvalue else arg.name for arg in self.params]
            )
            param_s = "*%s*" % param_s
        out += "#### %s(%s) \n\n" % (self.name, param_s)

        if self.comments is not None and self.comments.strip() != "":
            out += "```\n" + self.comments + "\n```\n\n"

        return out

    def __repr__(self):
        return self.__str__()


class ClassDoc(j.baseclasses.object):
    def __init__(self, classobj, location):
        JSBASE.__init__(self)
        self.location = location
        self.methods = {}
        self.comments = inspect.getdoc(classobj)
        module = inspect.getmodule(classobj)
        self.path = inspect.getabsfile(module)
        self.errors = ""
        self.properties = []
        for key, val in classobj.__dict__.items():
            if key.startswith("_"):
                continue
            self.properties.append(key)

    def getPath(self):
        for method in self.methods:
            return inspect.getabsfile(method)

    def addMethod(self, name, method):
        try:
            source = inspect.getsource(method)
        except BaseException:
            self.errors += "#### Error trying to add %s source in %s.\n" % (name, self.location)

        self._log_debug("ADD METHOD:%s %s" % (self.path, name))
        md = MethodDoc(method, name, self)
        self.methods[name] = md
        return source, md.params

    def undersore_location(self):
        return self.location.replace(".", "_")

    def write(self, dest):
        dest2 = j.sal.fs.joinPaths(dest, self.location.split(".")[1], "%s.md" % self.undersore_location())
        destdir = j.sal.fs.getDirName(dest2)
        j.sal.fs.createDir(destdir)
        content = str(self)
        content = content.replace("\n\n\n", "\n\n")
        content = content.replace("\n\n\n", "\n\n")
        content = content.replace("\n\n\n", "\n\n")

        # ugly temp hack, better to do with regex
        content = content.replace(r"\{", "$%[")
        content = content.replace(r"\}", "$%]")
        content = content.replace("{", r"\{")
        content = content.replace("}", r"\}")
        content = content.replace("$%]", r"\}")
        content = content.replace("$%[", r"\{")

        j.sal.fs.writeFile(filename=dest2, contents=content)
        return dest2

    def __str__(self):
        C = "<!-- toc -->\n"
        C += "## %s\n\n" % self.location
        C += "- %s\n" % self.path
        if self.properties != []:
            C += "- Properties\n"
            for prop in self.properties:
                C += "    - %s\n" % prop
        C += "\n### Methods\n"
        C += "\n"

        if self.comments is not None:
            C += "\n%s\n\n" % self.comments

        keys = sorted(self.methods.keys())
        for key in keys:
            method = self.methods[key]
            C2 = str(method)
            C += C2
        return C

    def __repr__(self):
        return self.__str__()


class ObjectInspector(j.baseclasses.object):

    """
    functionality to inspect object structure and generate apifile
    and pickled ordereddict for codecompletion
    """

    __jslocation__ = "j.tools.objectinspector"

    def _init(self, **kwargs):
        self.apiFileLocation = j.sal.fs.joinPaths(j.dirs.CFGDIR, "codecompletionapi", "api")
        # j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.JSCFGDIR, "codecompletionapi"))
        self.classDocs = {}
        self.visited = []
        self.root = None
        self.manager = None

        # jstree['j.sal']={'unix': unixobject, 'fs': fsobject}
        self.jstree = OrderedDict()

    def importAllLibs(self, ignore=[], base="%s/lib/Jumpscale/" % j.dirs.BASEDIR):
        self.base = os.path.normpath(base)
        towalk = j.sal.fs.listDirsInDir(base, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)
        errors = "### errors while trying to import libraries\n\n"
        for item in towalk:

            path = "%s/%s" % (base, item)
            for modname in j.sal.fs.listDirsInDir(path, False, True, True):
                if modname not in ignore:
                    toexec = "import %s.%s" % (item, modname)
                    try:
                        exec(toexec)
                    except Exception as e:
                        self._log_error(("COULD NOT IMPORT %s" % toexec))
                        errors += "**%s**\n\n" % toexec
                        errors += "%s\n\n" % e
        return errors

    def raiseError(self, errormsg):
        self._log_error("ERROR:%s" % errormsg)
        errormsg = errormsg.strip()
        errormsg = errormsg.strip("-")
        errormsg = errormsg.strip("*")
        errormsg = errormsg.strip()
        errormsg = "* %s\n" % errormsg
        j.sal.fs.writeFile(filename="%s/errors.md" % self.dest, contents=errormsg, append=True)

    def generateDocs(self, dest, ignore=[], objpath="j"):
        """
        Generates documentation of objpath in destination direcotry dest
        @param dest: destination directory to write documentation.
        @param objpath: object path
        @param ignore: modules list to be ignored during the import.

        """
        self.dest = dest
        self.apiFileLocation = "%s/api" % self.dest
        j.sal.fs.writeFile("%s/errors.md" % dest, "")
        j.sal.fs.createDir(self.dest)
        self.errors = self.importAllLibs(ignore=ignore)
        # self.errors = ''
        objectLocationPath = objpath

        # extract the object name (j.sal.unix ) -> unix to make a stub out of
        # it.
        objname = ""
        filepath = ""
        if "." in objpath:
            objname = objpath.split(".")[-1]
        else:
            objname = objpath
        try:
            obj = eval(objpath)
            if "__file__" in dir(obj):
                filepath = inspect.getabsfile(obj.__file__)
                if not filepath.startswith(self.base):
                    return
            else:

                filepath = inspect.getfile(obj.__class__)
                if not filepath.startswith(self.base):
                    return
        except BaseException:
            pass

        # add the root object to the tree (self.jstree) as its first element
        # (order maintained by ordereddict/pickle)
        self.jstree[objectLocationPath] = attrib(objname, "class", "emptydocs", objectLocationPath)
        self.inspect(objectLocationPath)
        j.sal.fs.createDir(dest)
        j.sal.fs.writeFile(filename="%s/errors.md" % dest, contents=self.errors, append=True)
        self.writeDocs(dest)

    def _processMethod(self, name, method, path, classobj):
        if classobj is None:
            raise j.exceptions.RuntimeError("cannot be None")

        classpath = ".".join(path.split(".")[:-1])

        if classpath not in self.classDocs:
            self.classDocs[classpath] = ClassDoc(classobj, classpath)
        obj = self.classDocs[classpath]
        return obj.addMethod(name, method)

    def _processClass(self, name, path, classobj):
        if path not in self.classDocs:
            self.classDocs[path] = ClassDoc(classobj, path)
        obj = self.classDocs[path]

    def inspect(self, objectLocationPath="j", recursive=True, parent=None, obj=None):
        """
        walk over objects in memory and create code completion api in jumpscale cfgDir under codecompletionapi
        @param object is start object
        @param objectLocationPath is full location name in object tree e.g. j.sal.fs , no need to fill in
        """
        self._log_debug(objectLocationPath)
        if obj is None:
            try:
                obj = eval(objectLocationPath)
            except BaseException:
                self.raiseError("could not eval:%s" % objectLocationPath)
                return
        # only process our files
        try:
            if "__file__" in dir(obj):
                filepath = inspect.getabsfile(obj.__file__)
                filepath = os.path.normpath(filepath)  # normalize path
                if not filepath.startswith(self.base):
                    return
            else:
                clsfile = inspect.getfile(obj.__class__)
                clsfile = os.path.normpath(clsfile)
                if not clsfile.startswith(self.base):
                    return
        except Exception as e:
            # print "COULD NOT DEFINE FILE OF:%s"%objectLocationPath
            pass

        if obj not in self.visited and obj:
            self.visited.append(obj)
        else:
            self._log_debug("RECURSIVE:%s" % objectLocationPath)
            return
        attrs = dir(obj)

        ignore = ["constructor_args", "NOTHING", "template_class", "redirect_cache"]

        def check(item):
            if item == "_getFactoryEnabledClasses":
                return True
            if item.startswith("_"):
                return False
            if item.startswith("im_"):
                return False
            if item in ignore:
                return False
            return True

        # if objectLocationPath == 'j.actions.logger.disabled':

        attrs = [item for item in attrs if check(item)]

        for objattributename in attrs:
            filepath = None
            objectLocationPath2 = "%s.%s" % (objectLocationPath, objattributename)
            try:
                objattribute = eval("obj.%s" % objattributename)
            except Exception as e:
                self._log_error(str(e))
                self.raiseError("cannot eval %s" % objectLocationPath2)
                continue
            if objattributename.upper() == objattributename:
                # is special type or constant
                self._log_debug("special type: %s" % objectLocationPath2)
                j.sal.fs.writeFile(self.apiFileLocation, "%s?7\n" % objectLocationPath2, True)
                self.jstree[objectLocationPath2] = attrib(objattributename, "const", "", objectLocationPath2, filepath)

            elif objattributename == "_getFactoryEnabledClasses":
                try:
                    for fclparent, name, obj2 in obj._getFactoryEnabledClasses():
                        if fclparent != "":
                            objectLocationPath2 = objectLocationPath + "." + fclparent + "." + name
                        else:
                            objectLocationPath2 = objectLocationPath + "." + name
                        self._processClass(name, objectLocationPath2, obj)
                        if not isinstance(objattribute, (str, bool, int, float, dict, list, tuple)):
                            self.inspect(objectLocationPath=objectLocationPath2, recursive=True, parent=obj, obj=obj2)

                except Exception as e:
                    self._log_error("the _getFactoryEnabledClasses gives error")
                    import ipdb
            elif (
                inspect.isfunction(objattribute)
                or inspect.ismethod(objattribute)
                or inspect.isbuiltin(objattribute)
                or inspect.isgenerator(objattribute)
            ):
                # isinstance(objattribute, (types.BuiltinMethodType,
                # types.BuiltinFunctionType, types.MethodType,
                # types.FunctionType)):
                try:
                    methodpath = inspect.getabsfile(objattribute)
                    methodargs = ", ".join(objattribute.__code__.co_varnames)
                    filepath = methodpath
                    if not methodpath.startswith(self.base):
                        self.classDocs.pop(objectLocationPath2, "")
                        self._log_info("SKIPPED:%s" % objectLocationPath2)
                        return
                except Exception as e:
                    self._log_error(str(e))

                source, params = self._processMethod(objattributename, objattribute, objectLocationPath2, obj)
                self._log_debug("instancemethod: %s" % objectLocationPath2)
                j.sal.fs.writeFile(self.apiFileLocation, "%s?4(%s)\n" % (objectLocationPath2, params), True)
                self.jstree[objectLocationPath2] = attrib(
                    objattributename, "method", objattribute.__doc__, objectLocationPath2, filepath, methodargs
                )

            elif isinstance(objattribute, (str, bool, int, float, list, tuple, dict, property)) or objattribute is None:
                self._log_debug("property: %s" % objectLocationPath2)
                j.sal.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)
                self.jstree[objectLocationPath2] = attrib(
                    objattributename, "property", objattribute.__doc__, objectLocationPath2
                )

            elif isinstance(objattribute.__class__, type):
                j.sal.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)
                self._log_debug("class or instance: %s" % objectLocationPath2)
                try:
                    filepath = inspect.getfile(objattribute.__class__)
                except BaseException:
                    pass
                self.jstree[objectLocationPath2] = attrib(
                    objattributename, "class", objattribute.__doc__, objectLocationPath2, filepath
                )
                try:
                    if (
                        not isinstance(objattribute, (str, bool, int, float, dict, list, tuple))
                        or objattribute is not None
                    ):
                        self.inspect(objectLocationPath2, parent=objattribute)
                except Exception as e:
                    self._log_error(str(e))
            else:
                pass

    def writeDocs(self, path):
        """
        Writes the documentation on a specified path.
        """
        self.dest = os.path.normpath(self.dest)
        todelete = []
        summary = {}
        for key, doc in list(self.classDocs.items()):
            # root items (data,core,application, sal,..)
            key2 = ".".join(key.split(".")[0:2])
            if key2 not in summary:
                summary[key2] = {}
            dest = doc.write(path)
            # remember gitbook info
            dest = os.path.normpath(dest)
            summary[key2][key] = j.sal.fs.pathRemoveDirPart(dest, self.dest)

        summarytxt = ""
        keys1 = sorted(summary.keys())
        for key1 in keys1:
            summarytxt += "* %s\n" % (key1)
            keys2 = sorted(summary[key1].keys())
            for key2 in keys2:
                keylink = summary[key1][key2]
                keylink = keylink.rstrip(".md").replace(".", "_")
                keylink = keylink + ".md"
                summarytxt += "    * [%s](%s)\n" % (key2, keylink)

        j.sal.fs.writeFile(filename="%s/SUMMARY.md" % (self.dest), contents=summarytxt)

        with open("%s/out.pickled" % self.dest, "wb") as f:
            import pickle

            pickle.dump(self.jstree, f)
            # json.dump(self.jstree,  f, indent=4, sort_keys=True)
