# from baselib.codeexecutor.CodeExecutor import CodeExecutor
import inspect
from Jumpscale import j

from .ClassBase import ClassBase, JSModelBase, JSRootModelBase
from .TemplateEngine import TemplateEngine
from .TextFileEditor import TextFileEditor
from .ReplaceTool import ReplaceTool


# ujson.dumps does not support some arguments like separators, indent ...etc
JSBASE = j.baseclasses.object


def isPrimAttribute(obj, key):
    if key[-1] == "s":
        funcprop = "new_%s" % key[:-1]
    else:
        funcprop = "new_%s" % key
    isprimtype = not hasattr(obj, funcprop)
    return isprimtype, funcprop


class Struct(j.baseclasses.object):
    def __init__(self, **kwargs):
        JSBASE.__init__(self)
        self.__dict__.update(kwargs)


class CodeTools(j.baseclasses.object):
    __jslocation__ = "j.tools.code"

    def _init(self, **kwargs):
        self._templateengine = None
        # self.executor = CodeExecutor()
        self._wordreplacer = None
        # self._codemanager = None
        self._texteditor = None

    # @property
    # def codemanager(self):
    #     if self._codemanager is None:
    #         from CodeManager import CodeManager
    #         self._codemanager = CodeManager()
    #     return self._codemanager

    def template_engine_get(self):
        return TemplateEngine()

    def text_editor_get(self, path):
        return TextFileEditor(path)

    def replace_tool_get(self):
        if self._wordreplacer is None:
            self._wordreplacer = ReplaceTool()
        return self._wordreplacer

    def textToTitle(self, text, maxnrchars=60):
        """
        try to create a title out of text, ignoring irrelevant words and making lower case and removing
        not needed chars
        """
        ignore = "for in yes no after up down the"
        ignoreitems = ignore.split(" ")
        keepchars = "abcdefghijklmnopqrstuvwxyz1234567890 "
        out = ""
        text = text.lower().strip()
        for char in text:
            if char in keepchars:
                out += char
        text = out
        text = text.replace("  ", "")
        text = text.replace("  ", "")
        out = ""
        nr = 0
        for item in text.split(" "):
            if item not in ignoreitems:
                nr += len(item)
                if nr < maxnrchars:
                    out += item + " "
        if len(text.split(" ")) > 0:
            text = out.strip()
        if len(text) > maxnrchars:
            text = text[:maxnrchars]
        return text

    def classInfoPrint(self, classs):
        """
        print info like source code of class
        """
        filepath, linenr, sourcecode = self.classInfoGet(classs)
        self._log_debug(("line:%s in path:%s" % (linenr, filepath)))
        self._log_debug(sourcecode)

    def classInfoGet(self, classs):
        """
        returns filepath,linenr,sourcecode
        """
        code, nr = inspect.getsourcelines(classs.__class__)
        code = "".join(code)
        path = inspect.getsourcefile(classs.__class__)
        return path, nr, code

    # def classEditGeany(self, classs):
    #     """
    #     look for editor (uses geany) and then edit the file
    #     """
    #     filepath, linenr, sourcecode = self.classInfoGet(classs)
    #     j.sal.process.executeWithoutPipe("geany %s" % filepath)

    def classGetBase(self):
        return ClassBase

    # def classGetAppserver6GreenletSchedule(self):
    #     return Appserver6GreenletScheduleBase

    # def classGetAppserver6Greenlet(self):
    #     return Appserver6GreenletBase

    # def classGetAppserver6GreenletTasklets(self):
    #     return Appserver6GreenletTaskletsBase

    def dict2object(self, obj, data):
        if obj is None:
            return Struct(**data)
        if hasattr(obj, "_dict2obj"):
            return obj._dict2obj(data)
        if isinstance(data, dict):
            for key, value in list(data.items()):
                # is for new obj functionname
                objpropname = "%s" % key

                if isinstance(value, dict) and isinstance(obj.__dict__[objpropname], dict):
                    # is a real dict (not a dict as representation of an object)
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        raise j.exceptions.RuntimeError("not supported")
                    else:
                        for valkey, valval in list(value.items()):
                            attr = getattr(obj, key)
                            attr[valkey] = valval

                elif isinstance(data[key], list):
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valval in value:
                            newobj = method()
                            self.dict2object(newobj, valval)
                    else:
                        for (valval,) in value:
                            attr = getattr(obj, key)
                            attr.append(valval)

                elif isinstance(value, dict) and not isinstance(obj.__dict__[objpropname], dict):
                    # is a dict which represents another object
                    raise j.exceptions.RuntimeError("not supported, only 1 level deep objects")
                else:
                    obj.__dict__[objpropname] = value
            return obj
        else:
            return data

    def dict2JSModelobject(self, obj, data):
        if isinstance(data, dict):
            for key, value in list(data.items()):
                # is for new obj functionname
                objpropname = "_P_%s" % key if not key.startswith("_P_") else key

                if isinstance(value, dict) and isinstance(obj.__dict__[objpropname], dict):
                    # is a real dict (not a dict as representation of an object)
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valkey, valval in list(value.items()):
                            newobj = method(valkey)
                            self.dict2JSModelobject(newobj, valval)
                    else:
                        for valkey, valval in list(value.items()):
                            attr = getattr(obj, key)
                            attr[valkey] = valval

                elif isinstance(value, list):
                    if key == "_meta":
                        # we do not duplicate meta
                        continue
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valval in value:
                            newobj = method()
                            self.dict2JSModelobject(newobj, valval)
                    else:
                        for valval in value:
                            attr = getattr(obj, key)
                            attr.append(valval)

                elif isinstance(value, dict) and not isinstance(obj.__dict__[objpropname], dict):
                    # is a dict which represents another object
                    obj.__dict__[objpropname] = self.dict2JSModelobject(obj.__dict__[objpropname], value)
                else:
                    obj.__dict__[objpropname] = value
            return obj
        else:
            return data

    # def dict2object2(self,d):
    # if isinstance(d, dict):
    # n = {}
    # for item in d:
    # if isinstance(d[item], dict):
    # n[item] = dict2obj(d[item])
    # elif isinstance(d[item], (list, tuple)):
    # n[item] = [dict2obj(elem) for elem in d[item]]
    # else:
    # n[item] = d[item]
    # return type('obj_from_dict', (object,), n)
    # else:
    # return d

    def object2dict4index(self, obj):
        """
        convert object to a dict
        only properties on first level are considered
        and properties of basic types like int,str,float,bool,dict,list
        ideal to index the basics of an object
        """
        result = {}

        def toStr(obj, possibleList=True):
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return str(obj)
            elif possibleList and j.data.types.list.check(obj):
                r = ""
                for item in obj:
                    rr = toStr(obj, possibleList=False)
                    if rr != "":
                        r += "%s," % rr
                r = r.rstrip(",")
                return r
            return ""

        if isinstance(obj, ClassBase):
            for key, value in list(obj.__dict__.items()):
                if key[0:3] == "_P_":
                    key = key[3:]
                elif key[0] == "_":
                    continue
                if j.data.types.dict.check(value):
                    for key2 in list(value.keys()):
                        r = toStr(value[key2])
                        if r != "":
                            result["%s.%s"(key, key2)] = r
                else:
                    r = toStr(value)
                    if r != "":
                        result[key] = r
        return result

    def object2dict(self, obj, dieOnUnknown=False, ignoreKeys=[], ignoreUnderscoreKeys=False):
        if j.data.types.dict.check(obj):
            return obj
        data = {}

        def todict(obj, data, ignoreKeys):
            if isinstance(obj, dict):
                value = {}
                for key in list(obj.keys()):
                    if key in ignoreKeys:
                        continue
                    if ignoreUnderscoreKeys and key and key[0] == "_":
                        continue
                    value[key] = todict(obj[key], {}, ignoreKeys)
                return value
            elif isinstance(obj, (tuple, list)):
                value = []
                for item in obj:
                    value.append(todict(item, {}, ignoreKeys))
                return value
            elif isinstance(obj, str):
                return obj.encode("utf8")
            elif isinstance(obj, (int, str, float, bool)) or obj is None:
                return obj
            elif isinstance(obj, bytes) or obj is None:
                return obj.decode("utf-8", "ignore")
            elif isinstance(obj, ClassBase):
                if hasattr(obj, "_obj2dict"):
                    return obj._obj2dict()
                else:
                    for key, value in list(obj.__dict__.items()):
                        if key[0:3] == "_P_":
                            key = key[3:]
                        if key in ignoreKeys:
                            continue
                        elif ignoreUnderscoreKeys and key[0] == "_":
                            continue
                        data[key] = todict(value, {}, ignoreKeys)
                return data
            else:
                # from core.Shell import ipshellDebug,ipshell
                # self._log_debug "DEBUG NOW Can only convert object to dict with properties basic types or inherited of ClassBase"
                # ipshell()
                if dieOnUnknown:
                    raise j.exceptions.RuntimeError(
                        "Can only convert object to dict with properties basic types or inherited of ClassBase"
                    )
                try:
                    val = str(value)
                except BaseException:
                    val = "__UNKNOWN__"
                return val

        out = todict(obj, data, ignoreKeys)
        return out

    def object2yaml(self, obj):
        return j.data.serializers.yaml.dumps(self.object2dict(obj))

    def object2json(self, obj, pretty=False, skiperrors=False, ignoreKeys=[], ignoreUnderscoreKeys=False):
        obj = self.object2dict(
            obj, dieOnUnknown=not skiperrors, ignoreKeys=ignoreKeys, ignoreUnderscoreKeys=ignoreUnderscoreKeys
        )
        if pretty:
            return j.data.serializers.json.dumps(obj, indent=2, sort_keys=True)
        else:
            return j.data.serializers.json.dumps(obj)

    def pprint(self, obj):
        result = self.object2yaml(obj)
        result = result.replace("!!python/unicode", "")
        self._log_debug(result)

    def deIndent(self, content, level=1):
        for i in range(0, level):
            content = self._deIndent(content)
        return content

    def indent(self, content, level=1):
        if not content:
            return content
        if content[-1] == "\n":
            content = content[:-1]
        lines = list()
        for line in content.splitlines():
            indent = " " * 4 * level
            lines.append("%s%s\n" % (indent, line))
        return "".join(lines)

    def _deIndent(self, content):
        # remove garbage & fix identation
        content2 = ""
        for line in content.split("\n"):
            if line.strip() == "":
                content2 += "\n"
            else:
                if line.find("    ") != 0:
                    raise j.exceptions.RuntimeError("identation error for %s." % content)
                content2 += "%s\n" % line[4:]
        return content2
