import time
import re
import socket

# import os
import textwrap
import unicodedata
import math
from unidecode import unidecode

matchquote = re.compile(r"\'[^\']*\'")
matchlist = re.compile(r"\[[^\']*\]")
re_nondigit = re.compile(r"\D")
re_float = re.compile(r"[0-9]*\.[0-9]+")
re_digit = re.compile(r"[0-9]*")

# _ansi_regex = (
#     r"\x1b("
#     r"(\[\??\d+[hl])|"
#     r"([=<>a-kzNM78])|"
#     r"([\(\)][a-b0-2])|"
#     r"(\[\d{0,2}[ma-dgkjqi])|"
#     r"(\[\d+;\d+[hfy]?)|"
#     r"(\[;?[hf])|"
#     r"(#[3-68])|"
#     r"([01356]n)|"
#     r"(O[mlnp-z]?)|"
#     r"(/Z)|"
#     r"(\d+)|"
#     r"(\[\?\d;\d0c)|"
#     r"(\d;\dR))"
# )
# re_ansi = re.compile(_ansi_regex, flags=re.IGNORECASE)
try:
    import colors
except:
    colors = None
from builtins import str

try:
    import pygments.lexers

    # from pygments.formatters import get_formatter_by_name
    pygmentsObj = True
    import sys
except BaseException:
    pygmentsObj = False

mascot = """
                                                        .,,'
                                                   'c.cool,..',,,,,,,.
                                                  'dxocol:l:;,'......';:,.
                                              .lodoclcccc,...............;:.
                                                ':lc:;;;;;.................:;
            JUMPSCALE                         :oc;'..................,'.....,;
            ---------                        olc'.......'...........,. .,:'..:.
                                            ,oc'......;,',..........od.   'c..'
                                            ;o:......l,   ':........dWkkN. ,;..
                                            .d;.....:K. ;   l'......:KMMM: ''.';'
                                             :,.....cNWNMx  .o.......;OWNc,.....,c
                                              c.....'kMMMX   l.........,,......;'c.
                                             l........xNNx...,. 'coxk;',;;'....;xd.
                                            .l..,...........';;;:dkkc::;;,.....'l'
                                             o'x............lldo,.'o,cl:;'...;,;;
                                           ..;dd'...........':'.,lkkk,.....,.l;l
                                       .',,....'l'.co..;'..........'.....;d,;:
                                    ';;..........;;o:c;,dl;oc,'......';;locc;
                                 ,:;...................;;:',:'',,,,,'.      .,.
                              .::.................................            'c
                            .:,...................................           . .l
                          .:,......................................          'l':
                        .;,.......................................            .l.
                     ';c:.........................................          ;:.';
              ',;::::'...........................................            :d;l;.
           'lolclll,,'..............................','..........            .dccco;
          loooool:,'..............................'l'..........     '.       cocclll..
        .lol:;'...................................::.,,'........    .o     .ldcccccccco:
       ,lcc'.........,;...,;.    ................',c:,''........,.  .o   .;;xccccccccld:
        .';ccc:;;,,'.  ...  ..''..             ;;'...............';.c'.''.  ;loolloooo;
                                ..',,,,,,,''...:o,.................c           ....
                                               .;l.................c.
                                                 ;;;;,'..........,;,
                                                    .':ldddoooddl
"""


class Text(object):
    def __init__(self, j):
        self._j = j
        self.mascot = mascot

    def unicodedata(self, text):
        return unicodedata.normalize("NFKD", text.decode("utf-8")).encode("ascii", "ignore")

    def strip_to_ascii(self, text):
        return "".join([char for char in str(text) if ((ord(char) > 31 and ord(char) < 127) or ord(char) == 10)])

    def convert_to_snake_case(self, text):
        converted_string = re.sub("([^/_.])([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", converted_string).lower()

    def strip_to_ascii_dense(self, text):
        """
        convert to ascii converting as much as possibe to ascii
        replace -,:... to _
        lower the text
        remove all the other parts
        
        """
        text = unidecode(text)  # convert to ascii letters
        # text=self.strip_to_ascii(text) #happens later already
        text = text.lower()
        text = text.replace("\n", "")
        text = text.replace("\t", "")
        text = text.replace(" ", "")
        text = self.ansi_remove(text)

        def replace(char):
            if char in "-/\\= ;!+()":
                return "_"
            return char

        def check(char):
            charnr = ord(char)
            if char in "._":
                return True
            if charnr > 47 and charnr < 58:
                return True
            if charnr > 96 and charnr < 123:
                return True
            return False

        res = [replace(char) for char in str(text)]
        res = [char for char in res if check(char)]
        text = "".join(res)
        while "__" in text:
            text = text.replace("__", "_")
        text = text.rstrip("_")
        return text

    def pad(self, text, length):
        while len(text) < length:
            text += " "
        return text

    # def stripItems(self, line, items=["PATH", "\"", " ", "'", ":", "${PATH}", "=", ","]):
    #     def checknow(line, items):
    #         found = False
    #         for item in items:
    #             if line.startswith(item):
    #                 line = line[len(item):]
    #                 found = True
    #             if line.endswith(item):
    #                 line = line[:-len(item)]
    #                 found = True
    #         return found, line
    #
    #     res, line = checknow(line, items)
    #     while res:
    #         res, line = checknow(line, items)
    #     return line

    def strToVersionInt(self, versionStr, minDigits=3):
        """
        convert 3.2.1 to 3002001
        convert 3 to 3000000
        """
        if "." in versionStr:
            splitted = versionStr.split(".")
        else:
            splitted = versionStr.split(",")
        while len(splitted) < minDigits:
            splitted.append("0")
        y = 0
        splitted.reverse()
        x = 0
        for item in splitted:
            y += int(math.pow(1000, x)) * int(splitted[x])
            x += 1
        return y

    def toStr(self, value, codec="utf-8"):
        if isinstance(value, bytes):
            value = value.decode(codec)
        return value

    def toSafePath(self, txt, maxlen=0):
        """
        process string so it can be used in a path on windows or linux
        """
        txt = self.toAscii(txt)
        txt = txt.lower().strip().strip(" .-_'")
        txt = (
            txt.replace("/", "")
            .replace(",", " ")
            .replace("*", "")
            .replace("(", "")
            .replace(")", "")
            .replace('"', "")
            .replace("?", "")
            .replace("'", "")
            .replace(":", " ")
        )
        while txt.find("  ") != -1:
            txt = txt.replace("  ", " ")
        if maxlen > 0 and len(txt) > maxlen:
            txt = txt[0:maxlen]
        return txt.strip()

    def ansi_remove(self, txt):
        if colors:
            return colors.strip_color(txt)
        else:
            return txt
        # return re_ansi.sub("", txt)

    def toAscii(self, value, maxlen=0):
        value = value.strip()
        while "  " in value:
            value = value.replace("  ", " ")
        value = self.ansi_remove(value)
        ok = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_!. {}()':"
        value.replace('"', "'")
        value.replace("`", "'")
        out = ""
        for c in value:
            if c in ok:
                out += c
        if maxlen > 0 and len(out) > maxlen:
            out = out[0:maxlen]

        return out.strip()

    def indent(self, instr, nspaces=4, wrap=180, strip=True, indentchar=" ", args=None):
        """Indent a string a given number of spaces.

        Parameters
        ----------

        instr : basestring
            The string to be indented.
        nspaces : int (default: 4)
            The number of spaces to be indented.

        Returns
        -------

        str|unicode : string indented by ntabs and nspaces.

        """
        return self._j.core.tools.text_indent(
            instr, nspaces=nspaces, wrap=wrap, strip=strip, indentchar=indentchar, args=args
        )

    def toUnicode(self, value, codec="utf-8"):
        if isinstance(value, str):
            return value.decode(codec)
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def strip(self, content, ignorecomments=True, args={}, replace=False):
        if replace:
            return self._j.core.tools.text_replace(content=content, ignorecomments=ignorecomments, args=args)
        else:
            return self._j.core.tools.text_strip(content=content, ignorecomments=ignorecomments)

    def sort(self, txt):
        """
        removes all empty lines & does a sort
        """
        return "\n".join([item for item in sorted(txt.split("\n")) if item != ""]) + "\n"

    def prefix(self, prefix, txt):
        out = ""
        txt = txt.rstrip("\n")
        for line in txt.split("\n"):
            out += "%s%s\n" % (prefix, line)
        return out

    def wrap(self, txt, length=120):
        return self._j.core.tools.text_wrap(txt=txt, length=length)

    def prefix_remove(self, prefix, txt, onlyPrefix=False):
        """
        @param onlyPrefix if True means only when prefix found will be returned, rest discarded
        """
        out = ""
        txt = txt.rstrip("\n")
        l = len(prefix)
        for line in txt.split("\n"):
            if line.find(prefix) == 0:
                out += "%s\n" % (line[l:])
            elif onlyPrefix is False:
                out += "%s\n" % (line)
        return out

    def prefix_remove_withtrailing(self, prefix, txt, onlyPrefix=False):
        """
        there can be chars for prefix (e.g. '< :*: aline'  and this function looking for :*: would still work and ignore '< ')
        @param onlyPrefix if True means only when prefix found will be returned, rest discarded
        """
        out = ""
        txt = txt.rstrip("\n")
        # l = len(prefix)
        for line in txt.split("\n"):
            if line.find(prefix) > -1:
                out += "%s\n" % (line.split(prefix, 1)[1])
            elif onlyPrefix is False:
                out += "%s\n" % (line)
        return out

    def addCmd(self, out, entity, cmd):
        out += "!%s.%s\n" % (entity, cmd)
        return out

    def addTimeHR(self, line, epoch, start=50):
        if int(epoch) == 0:
            return line
        while len(line) < start:
            line += " "
        line += "# " + time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(int(epoch)))
        return line

    def addVal(self, out, name, val, addtimehr=False):
        if isinstance(val, int):
            val = str(val)
        while len(val) > 0 and val[-1] == "\n":
            val = val[:-1]
        if len(val.split("\n")) > 1:
            out += "%s=...\n" % (name)
            for item in val.split("\n"):
                out += "%s\n" % (item)
            out += "...\n"
        else:
            line = "%s=%s" % (name, val)
            if addtimehr:
                line = self.addTimeHR(line, val)
            out += "%s\n" % line
        return out

    def isNumeric(self, txt):
        return re_nondigit.search(txt) is None

    # def lstrip(self,content):
    #     """
    #     remove all spaces at beginning & end of line when relevant
    #     """
    #     #find generic prepend for full file
    #     minchars=9999
    #     prechars = 0
    #     for line in content.split("\n"):
    #         prechars=len(line)-len(line.lstrip())
    #         if prechars<minchars:
    #             minchars=prechars

    #     if prechars>0:
    #         #remove the prechars
    #         content="\n".join([line[minchars:] for line in content.split("\n")])
    #     return content

    def ask(self, content, name=None, args={}, ask=True):
        """
        look for @ASK statements in text, where found replace with input from user

        syntax for ask is:
            @ASK name:aname type:str descr:adescr default:adefault regex:aregex retry:10 minValue:10 maxValue:20 dropdownvals:1,2,3

            descr, default & regex can be between '' if spaces inside

            types are: str,float,int,bool,multiline,list

            retry means will keep on retrying x times until ask is done properly

            dropdownvals is comma separated list of values to ask for

        @ASK can be at any position in the text

        @return type,content

        """
        content = self.eval(content)
        if content.strip() == "":
            return None, content

        # endlf = content[-1] == "\n"
        ttype = None

        out = ""
        for line in content.split("\n"):

            # print ("ask:%s"%line)

            if line.find("@ASK") == -1 or not ask:
                out += "%s\n" % line
                continue

            result = "ERROR:UNKNOWN VAL FROM ASK"

            prefix, end = line.split("@ASK", 1)
            tags = self._j.data.tags.getObject(end.strip())

            if tags.tagExists("name"):
                name = tags.tagGet("name")
            else:
                if name is None:
                    if line.find("=") != -1:
                        name = line.split("=")[0].strip()
                    else:
                        name = ""

            if name in args:
                result = args[name]
                out += "%s%s\n" % (prefix, result)
                continue

            if name in args:
                result = args[name]
                out += "%s%s\n" % (prefix, result)
                continue

            if tags.tagExists("type"):
                ttype = tags.tagGet("type").strip().lower()
                if ttype == "string":
                    ttype = "str"
            else:
                ttype = "str"
            if tags.tagExists("descr"):
                descr = tags.tagGet("descr")
            else:
                if name != "":
                    descr = "Please provide value for %s of type %s" % (name, ttype)
                else:
                    descr = "Please provide value"

            # name=name.replace("__"," ")

            descr = descr.replace("__", " ")
            descr = descr.replace("\\n", "\n")

            if tags.tagExists("default"):
                default = tags.tagGet("default")
            else:
                default = ""

            if tags.tagExists("retry"):
                retry = int(tags.tagGet("retry"))
            else:
                retry = -1

            if tags.tagExists("regex"):
                regex = tags.tagGet("regex")
            else:
                regex = None

            if len(descr) > 30 and ttype not in ("dict", "multiline"):
                self._log_info(descr)
                descr = ""

            # print "type:'%s'"%ttype
            if ttype == "str":
                result = j.tools.console.askString(question=descr, defaultparam=default, regex=regex, retry=retry)

            elif ttype == "password":
                result = j.tools.console.askPassword(question=descr, confirm=False)

            elif ttype == "list":
                result = self._j.tools.console.askString(question=descr, defaultparam=default, regex=regex, retry=retry)

            elif ttype == "multiline":
                result = self._j.tools.console.askMultiline(question=descr)

            elif ttype == "float":
                result = self._j.tools.console.askString(question=descr, defaultparam=default, regex=None)
                # check getFloat
                try:
                    result = float(result)
                except BaseException:
                    raise self._j.exceptions.Input("Please provide float.", "system.self.ask.neededfloat")
                result = str(result)

            elif ttype == "int":
                if tags.tagExists("minValue"):
                    minValue = int(tags.tagGet("minValue"))
                else:
                    minValue = None

                if tags.tagExists("maxValue"):
                    maxValue = int(tags.tagGet("maxValue"))
                else:
                    maxValue = None

                if not default:
                    default = None
                result = self._j.tools.console.askInteger(
                    question=descr, defaultValue=default, minValue=minValue, maxValue=maxValue, retry=retry
                )

            elif ttype == "bool":
                if descr != "":
                    self._log_info(descr)
                result = self._j.tools.console.askYesNo()
                if result:
                    result = True
                else:
                    result = False

            elif ttype == "dropdown":
                if tags.tagExists("dropdownvals"):
                    dropdownvals = tags.tagGet("dropdownvals")
                else:
                    raise self._j.exceptions.Input(
                        "When type is dropdown in ask, then dropdownvals needs to be specified as well."
                    )
                choicearray = [item.strip() for item in dropdownvals.split(",")]
                result = self._j.tools.console.askChoice(choicearray, descr=descr, sort=True)
            elif ttype == "dict":
                rawresult = self._j.tools.console.askMultiline(question=descr)
                result = "\n"
                for line in rawresult.splitlines():
                    result += "    %s,\n" % line.strip().strip(",")

            else:
                raise self._j.exceptions.Input(
                    "Input type:%s is invalid (only: bool,int,str,string,dropdown,list,dict,float)" % ttype
                )

            out += "%s%s\n" % (prefix, result)

        # if endlf==False:
        out = out[:-1]
        return ttype, out

    def getMacroCandidates(self, txt):
        """
        look for \{\{\}\} return as list
        """
        result = []
        items = txt.split("{{")
        for item in items:
            if item.find("}}") != -1:
                item = item.split("}}")[0]
                if item not in result:
                    result.append("{{%s}}" % item)
        return result

    def _str2var(self, string):
        """
        try to check int or float or bool
        """
        if not isinstance(string, str):
            string = str(string)
        if string.lower() == "empty":
            return "n", None
        if string.lower() == "none":
            return "n", None
        if string == "":
            return "s", ""
        string2 = string.strip()
        if string2.lower() == "true":
            return "b", True
        if string2.lower() == "false":
            return "b", False
        # check int
        if re_nondigit.search(string2) is None and string2 != "":
            # print "int:'%s'"%string2
            return "i", int(string2)
        # check float
        match = re_float.search(string2)
        if match is not None and match.start() == 0 and match.end() == len(string2):
            return "f", float(string2)

        return "s", self.machinetext2str(string)

    def parseArgs(self, args):
        """
        @param args e.g.
            msg,f = 'f',g = 1, x=[1,2,3]

        result is dict with key the name, val is the default val
        if empty like for msg then None
        """
        args = args.rstrip("):")
        amMethodArgs = {}
        for arg in args.split(","):
            if "=" in arg:
                argname, default = arg.split("=", 1)
                argname = argname.strip()
                default = default.strip()
                if default[0] == '"':
                    default = default.strip('"')
                elif default[0] == "'":
                    default = default.strip("'")
                elif default == "[]":
                    default = []
                elif default == "{}":
                    default = {}
                elif default[0] in ("[", "{"):
                    default = eval(default)
                elif "." in default:
                    default = float(default)
                else:
                    default = int(default)
            else:
                argname = arg.strip()
                default = None
            amMethodArgs[argname] = default
        return amMethodArgs

    def parseDefLine(self, line, parseArgs=True):
        """
        will return name & args
        args is dict, with support for int, str, list, dict, float

        example line:
            def echo('f',g = 1, x=[1,2,3])
            async def echo('f',g = 1, x=[1,2,3])

        """
        # async = False
        definition = ""
        if line.find("async") == 0:
            # async = True
            line = line[len("async ") :]

        definition, args = line.split("(", 1)
        amName = definition[4:].strip()
        args = args.strip()
        if parseArgs:
            args = self.parseArgs(args)
        return amName, args

    def str2var(self, string):
        """
        convert list, dict of strings
        or convert 1 string to python objects
        """

        if self._j.data.types.list.check(string):
            ttypes = []
            for item in string:
                ttype, val = self._str2var(item)
                if ttype not in ttypes:
                    ttypes.append(ttype)
            if "s" in ttypes:
                result = [str(self.machinetext2val(item)) for item in string]
            elif "f" in ttypes and "b" not in ttypes:
                result = [self.getFloat(item) for item in string]
            elif "i" in ttypes and "b" not in ttypes:
                result = [self.getInt(item) for item in string]
            elif "b" == ttypes:
                result = [self.getBool(item) for item in string]
            else:
                result = [str(self.machinetext2val(item)) for item in string]
        elif self._j.data.types.dict.check(string):
            ttypes = []
            result = {}
            for key, item in list(string.items()):
                ttype, val = self._str2var(item)
                if ttype not in ttypes:
                    ttypes.append(ttype)
            if "s" in ttypes:
                for key, item in list(string.items()):
                    result[key] = str(self.machinetext2val(item))
            elif "f" in ttypes and "b" not in ttypes:
                for key, item in list(string.items()):
                    result[key] = self.getFloat(item)
            elif "i" in ttypes and "b" not in ttypes:
                for key, item in list(string.items()):
                    result[key] = self.getInt(item)
            elif "b" == ttypes:
                for key, item in list(string.items()):
                    result[key] = self.getBool(item)
            else:
                for key, item in list(string.items()):
                    result[key] = str(self.machinetext2val(item))
        elif isinstance(string, str) or isinstance(string, float) or isinstance(string, int):
            ttype, result = self._str2var(self._j.core.text.toStr(string))
        else:
            raise self._j.exceptions.Input(
                "Could not convert '%s' to basetype, input was %s. Expected string, dict or list."
                % (string, type(string)),
                "self.str2var",
            )
        return result

    def eval(self, code):
        """
        look for {{}} in code and evaluate as python result is converted back to str
        """
        candidates = self.getMacroCandidates(code)
        for item in candidates:
            if "{{" and "}}" in item:
                item = item.strip("{{").strip("}}")
            try:
                result = eval(item)
            except Exception as e:
                raise self._j.exceptions.RuntimeError(
                    "Could not execute code in self._j.core.text.,%s\n%s. Error was:%s" % (item, code, e)
                )
            result = self.pythonObjToStr(result, multiline=False).strip()
            code = code.replace(item, result)
        return code

    def pythonObjToStr1line(self, obj):
        return self.pythonObjToStr(obj, False, canBeDict=False)

    def pythonObjToStr(self, obj, multiline=True, canBeDict=True, partial=False):
        """
        try to convert a python object to string representation works for None, bool, integer, float, dict, list
        """
        if obj is None:
            return ""
        elif isinstance(obj, bytes):
            obj = obj.decode("utf8")
            return obj
        elif self._j.data.types.bool.check(obj):
            if obj:
                obj = "True"
            else:
                obj = "False"
            return obj
        elif self._j.data.types.string.check(obj):
            isdict = canBeDict and obj.find(":") != -1
            if obj.strip() == "":
                return ""
            if obj.find("\n") != -1 and multiline:
                obj = "\n%s" % self.prefix("    ", obj.strip())
            elif not isdict or obj.find(" ") != -1 or obj.find("/") != -1 or obj.find(",") != -1:
                if not partial:
                    obj = "'%s'" % obj.strip("'")
                else:
                    obj = "%s" % obj.strip("'")
            return obj
        elif self._j.data.types.int.check(obj) or self._j.data.types.float.check(obj):
            return str(obj)
        elif self._j.data.types.list.check(obj):
            obj.sort()
            tmp = []
            for item in obj:
                if item is None:
                    continue
                if isinstance(item, str):
                    if item.strip() == "" or item.strip() == "''":
                        continue
                tmp.append(item)
            obj = tmp
            # if not canBeDict:
            #     raise self._j.exceptions.RuntimeError("subitem cannot be list or dict for:%s"%obj)
            if multiline:
                resout = "\n"
                for item in obj:
                    resout += "    %s,\n" % self.pythonObjToStr1line(item)
                resout = resout.rstrip().strip(",") + ",\n"
            else:
                resout = "["
                for item in obj:
                    resout += "%s," % self.pythonObjToStr1line(item)
                resout = resout.rstrip().strip(",") + "]"

            return resout

        elif self._j.data.types.dict.check(obj):
            if not canBeDict:
                raise self._j.exceptions.RuntimeError("subitem cannot be list or dict for:%s" % obj)
            if multiline:
                resout = "\n"
                keys = sorted(obj.keys())
                for key in keys:
                    val = obj[key]
                    val = self.pythonObjToStr1line(val)
                    # resout+="%s:%s, "%(key,val)
                    resout += "    %s:%s,\n" % (key, self.pythonObjToStr1line(val))
                resout = resout.rstrip().rstrip(",") + ",\n"
            else:
                resout = ""
                keys = sorted(obj.keys())
                for key in keys:
                    val = obj[key]
                    val = self.pythonObjToStr1line(val)
                    resout += "%s:%s," % (key, val)
                resout = resout.rstrip().rstrip(",") + ","
            return resout

        else:
            raise self._j.exceptions.RuntimeError("Could not convert %s to string" % obj)

    def replaceQuotes(self, value, replacewith):
        for item in re.findall(matchquote, value):
            value = value.replace(item, replacewith)
        return value

    def machinetext2val(self, value):
        """
        do reverse of:
             SPACE -> \\S
             " -> \\Q
             , -> \\K
             : -> \\D
             \\n -> return
        """
        # value=value.strip("'")
        value2 = value.replace("\\K", ",")
        value2 = value2.replace("\\Q", '"')
        value2 = value2.replace("\\S", " ")
        value2 = value2.replace("\\D", ":")
        value2 = value2.replace("\\N", "\n")
        value2 = value2.replace("\\n", "\n")
        # change = False
        # if value != value2:
        #     change = True
        if value2.strip() == "":
            return value2
        if value2.strip().strip("'").startswith("[") and value2.strip().strip("'").endswith("]"):
            value2 = value2.strip().strip("'").strip("[]")
            res = []
            for item in value2.split(","):
                if item.strip() == "":
                    continue
                if self.isInt(item):
                    item = self.getInt(item)
                elif self.isFloat(item):
                    item = self.getFloat(item)
                res.append(item)
            return res

            # Check if it's not an ip address
            # because int/float test fails on "1.1.1.1" for example
            try:
                socket.inet_aton(value2)
            except socket.error:
                if self.isInt(value2):
                    return self.getInt(value2)
                elif self.isFloat(value2):
                    return self.getFloat(value2)
        # value2=value2.replace("\n","\\n")
        return value2

    def machinetext2str(self, value):
        """
        do reverse of:
             SPACE -> \\S
             " -> \\Q
             , -> \\K
             : -> \\D
             \n -> \\N
        """
        value = value.replace("\\K", ",")
        value = value.replace("\\Q", '"')
        value = value.replace("\\S", " ")
        value = value.replace("\\D", ":")
        value = value.replace("\\N", "\n")
        value = value.replace("\\n", "\n")
        return value

    def getInt(self, text):
        if self._j.data.types.string.check(text):
            text = self.strip(text).strip("'\"").strip()
            if text.lower() == "none":
                return 0
            elif text is None:
                return 0
            elif text == "":
                return 0
            else:
                text = int(text)
        else:
            text = int(text)
        return text

    def getFloat(self, text):
        if self._j.data.types.string.check(text):
            text = text.strip()
            if text.lower() == "none":
                return 0.0
            elif text is None:
                return 0.0
            elif text == "":
                return 0.0
            else:
                text = float(text)
        else:
            text = float(text)
        return text

    def isFloat(self, text):
        text = self.strip(",").strip()
        if not text.find(".") == 1:
            return False
        try:
            float(text)
            return True
        except ValueError:
            return False

    def isInt(self, text):
        text = self.strip(",").strip()
        return text.isdigit()

    def getBool(self, text):
        if self._j.data.types.bool.check(text):
            return text
        elif self._j.data.types.int.check(text):
            if text == 1:
                return True
            else:
                return False
        elif self._j.data.types.string.check(text):
            text = text.strip()
            if text.lower() == "none":
                return False
            elif text is None:
                return False
            elif text == "":
                return False
            elif text.lower() == "true":
                return True
            elif text == "1":
                return True
            else:
                return False
        else:
            raise self._j.exceptions.RuntimeError("input needs to be None, string, bool or int")

    # def _dealWithQuote(self, text):
    #     """
    #     look for 'something,else' the comma needs to be converted to \k
    #     """
    #     for item in re.findall(matchquote, text):
    #         text = text.replace(item, item)
    #     return text
    #
    # def _dealWithList(self, text):
    #     """
    #     look for [something,2] the comma needs to be converted to \k
    #     """
    #     for item in re.findall(matchlist, text):
    #         item2 = item.replace(",", "\\K")
    #         text = text.replace(item, item2)
    #     return text

    def getList(self, text, ttype=None):
        """
        @type can be int,bool or float (otherwise its always str)
        """

        # if already list just return
        if self._j.data.types.list.check(text):
            return text

        if text is None:
            return []

        if not self._j.data.types.string.check(text):
            raise j.exceptions.Base("need to be string:%s" % text)

        text = text.strip(" [")
        text = text.strip(" ]")

        text = text.strip('"').strip()

        if self.strip(text) == "":
            return []

        # text = self._dealWithQuote(text)  # to get ',' in '' not counting
        if "," in text:
            text = text.split(",")
            text = [item.strip().strip("'").strip() for item in text if item.strip().strip("'").strip() is not ""]
        elif "\n" in text:
            text = text.split("\n")
            text = [item.strip().strip("'").strip() for item in text if item.strip().strip("'").strip() is not ""]
        else:
            text = [text]

        if ttype is not None:
            ttype = self._j.data.types.get(ttype)
        else:
            ttype = self._j.data.types.string

        res = []
        for item in text:
            item = ttype.clean(item)
            if item not in res:
                res.append(item)
        return res

    def getDict(self, text, ttype=None):
        """
        keys are always treated as string
        @type can be int,bool or float (otherwise its always str)
        """
        if self.strip() == "" or self.strip() == "{}":
            return {}
        # text = self._dealWithList(text)
        # text = self._dealWithQuote(text)
        res2 = {}
        for item in self.split(","):
            if item.strip() != "":
                if item.find(":") == -1:
                    raise self._j.exceptions.RuntimeError("Could not find : in %s, cannot get dict out of it." % text)

                key, val = item.split(":", 1)
                if val.find("[") != -1:
                    val = self.machinetext2val(val)
                else:
                    # val = val.replace("\k", ",")
                    key = key.strip()
                    val = val.strip()
                res2[key] = val
        return res2

    def print(self, text, style="vim", lexer="bash"):
        """

        :param text:
        :param style: vim
        :param lexer: py3 or bash
        :return:
        """
        text = self.strip(text)
        formatter = pygments.formatters.Terminal256Formatter(style=pygments.styles.get_style_by_name(style))

        lexer = pygments.lexers.get_lexer_by_name(lexer)  # , stripall=True)
        colored = pygments.highlight(text, lexer, formatter)
        sys.stdout.write(colored)
