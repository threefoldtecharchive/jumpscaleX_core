method_replace = """
writeFile : file_write
readFile : file_read
j.sal.fs.writeFile : j.core.tools.file_write
j.sal.fs.readFile : j.core.tools.file_read
formatMessage : format_message
echoListItem : print_list_item
echoWithPrefix : print_with_prefix
echoListWithPrefix: print_with_prefix_list
echoDict : print_dict
transformDictToMessage
askString
askPassword
askInteger
askYesNo
askIntegers
askChoice
askChoiceMultiple : ask_choice_multiple
ask_choices : ask_choice
askMultiline
askArrayRow : ask_array_row
getOutput : output_get
hideOutput : output_hide
printOutput : output_print
enableOutput : output_enable
showArray : print_array
getMacroCandidates : macro_candidates_get
parseArgs : parse_python_arguments
parseDefLine : parse_python_method
pythonObjToStr1line : transform_pythonobject_1line
pythonObjToStr : transform_pythonobject_multiline
replaceQuotes : transform_quotes
j.core.tools.text_strip : j.data.text.strip
j.core.tools._check_interactive : j.tools.console.check_interactive
j.core.tools._j.core.myenv : j.core.myenv
j.core.tools.text_replace : j.data.text.replace
j.core.tools.text_strip : j.data.text.strip
j.core.tools.text_wrap : j.data.text.wrap
j.core.tools.text_replace : j.data.text.replace
j.core.tools.text_strip : j.data.text.strip
j.core.tools.text_wrap : j.data.text.wrap
j.core.tools.args_replace
j.core.tools._j.core.myenv.MYCOLORS
j.core.tools.text_strip_to_ascii_dense : j.data.text.strip_to_ascii_dense


"""

word_replace = """
.tools.ask_ : .tools.console.ask_
"""

# means there needs to be a . behind
obj_part_replace = """
Tools.exceptions : j.exceptions
Tools : j.core.tools
j.core.tools._j : j
"""

from pathlib import Path
import os
import inspect
import pudb
import re


class ReplacerTool:
    def __init__(self, left, right=None):
        self.left = left.strip()
        if not right:
            right = ""
            for char in left:
                if char != char.lower():
                    char = "_%s" % char.lower()
                right += char
        self.right = right.strip()

    def replace(self, txt):
        if txt.find(self.left) != -1:
            txt = txt.replace(self.left, self.right)
        return txt

    def __str__(self):
        return "%-40s: %s" % (self.left, self.right)

    __repr__ = __str__


class ReplacerToolObj(ReplacerTool):
    def replace(self, txt):
        if txt.startswith(self.left):
            txt = txt.replace(self.left, self.right)
        return txt


class CodeFixer:
    def __init__(self):

        self._replace_list_method = []
        self._replace_list_word = []
        self._replace_list_obj = []

        self._process_input(method_replace, self._replace_list_method)
        self._process_input(word_replace, self._replace_list_word)
        self._process_input(obj_part_replace, self._replace_list_obj, ReplacerToolObj)

    def _process_input(self, config, llist, klass=None):
        for line in config.split("\n"):
            if line.strip() == "":
                continue
            if line.strip().startswith("#"):
                continue
            if ":" in line:
                left, right = line.split(":", 1)
            else:
                right = None
                left = line
            if not klass:
                llist.append(ReplacerTool(left, right))
            else:
                llist.append(klass(left, right))

    def fix(self, path=None):
        self.walk(file_method=self._fix_file)

    def _fix_content(self, content):
        out = ""
        for line in content.split("\n"):
            out += "%s\n" % self._fix_line(line)
        return out

    def _fix_line(self, line):

        line = self._replace_word(line)

        # find obj parts e.g. j.exceptions
        regex = r"[\.\w]+\."
        x = 0
        m = None
        line_out = ""
        for m in re.finditer(regex, line):
            pre = m.string[x : m.start()]
            mid = m.string[m.start() : m.end() - 1]
            mid = self._replace_obj(mid)
            x = m.end()
            line_out += f"{pre}{mid}."
        if m:
            line_out += m.string[m.end() :]
            line = line_out

        # check for methods
        regex = r"[\.\w\-]+\("
        x = 0
        m = None
        line_out = ""
        for m in re.finditer(regex, line):
            pre = m.string[x : m.start()]
            mid = m.string[m.start() : m.end() - 1]
            mid = self._replace_method(mid)
            x = m.end()
            line_out += f"{pre}{mid}("
        if m:
            line_out += m.string[m.end() :]
            line = line_out

        return line

    def _replace_method(self, part):
        for r in self._replace_list_method:
            part = r.replace(part)
        return part

    def _replace_obj(self, part):
        for r in self._replace_list_obj:
            part = r.replace(part)
        return part

    def _replace_word(self, part):
        for r in self._replace_list_word:
            part = r.replace(part)
        return part

    def _fix_file(self, path):
        if path.name.find("CodeUpdater") != -1:
            return
        if "." not in path.name:
            return
        ext = path.name.split(".")[-1].lower()
        if not ext in ["py", "md", "txt"]:
            return
        content0 = path.read_text()
        for i in range(3):
            content1 = self._fix_content(content0)
        if content1.strip() != content0.strip():
            pass
            # path.write_text(content1)

    def walk(self, path=None, file_method=None):

        # a = self._fix_line("    def askChoice(self):")
        # b = self._fix_line("    def __init__(self):; askChoice(")
        # c = self._fix_line("    def j.core.tools.text_strip(   self)")
        # d = self._fix_line("abc( a,b,c)")
        # e = self._fix_line("(Tools.exceptions")
        # f = self._fix_line("Tools.exceptions(")
        # g = self._fix_line("Tools.exceptions.sdsd.sdsd")
        # h = self._fix_line("  Tools.(")
        # i = self._fix_line("j.core.tools._j.echo;def j.core.tools.text_strip(   self)")

        if not path:
            path = os.getcwd()

        p = Path(path)
        for dpath in p.iterdir():
            if dpath.name.startswith("."):
                continue
            if dpath.name.startswith("_"):
                continue
            dpath.absolute()
            if dpath.is_dir():
                self.walk(path=dpath.as_posix(), file_method=file_method)
            elif dpath.is_symlink():
                continue
            elif dpath.is_file():
                file_method(dpath)


cf = CodeFixer()

cf.fix()
