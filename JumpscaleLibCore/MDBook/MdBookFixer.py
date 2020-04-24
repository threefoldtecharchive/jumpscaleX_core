instructions_word_replace = """
something_not_existing : doesntapply
"""

from Tools import Tools
from MyEnv import MyEnv

myenv = MyEnv()

from pudb import set_trace as debug
import typing
from typing import Union, Optional

shell = Tools.shell
myenv = MyEnv
exceptions = Tools.exceptions

from pathlib import Path
import os

# import inspect
import re

Path2 = typing.TypeVar("Path2", None, Path)
StringNone = typing.TypeVar("StringNone", None, str)


class Link:
    def __init__(self, txt: str):
        # TODO: should be done better
        self.link = txt.split("(", 1)[1].split(")", 1)[0]
        self.descr = txt.split("(", 1)[0].strip(" []")


Link().link = 1


class ReplacerToolBaseItem:
    """
    has the knowledge how to replace code fragments based on an instructions file e.g. instructions_word_replace

    an instruction file is format

    ```
    $tofind
    $tofind : $replacewith

    the replacer tool only works on 1 line of the instruction file

    ```

    """

    pass


class ReplaceItem(ReplacerToolBaseItem):
    def __init__(self, left: str, right: Optional[str]):
        self.left = left.strip()
        if self.left.startswith("||"):
            # is a regex
            self.regex = True
        else:
            self.regex = False
        # makes camelcase, snakecase
        if not right:
            right = ""
            for char in left:
                if char != char.lower():
                    char = "_%s" % char.lower()
                right += char
        self.right = right.strip()

    def replace(self, txt: str) -> str:
        if self.regex:
            # TODO: need to implement regex support
            raise exceptions.Base("implement")
        else:
            if txt.find(self.left) != -1:
                txt = txt.replace(self.left, self.right)
        return txt

    def __str__(self):
        return "%-40s: %s" % (self.left, self.right)

    __repr__ = __str__


class ReplacerTool:
    def __init__(self, instruction_str: str):
        self._read_instructions(instruction_str)
        self._instructions: list(ReplacerToolBaseItem) = []

    def _read_instructions(self, config: str, llist: list, replacer: ReplacerToolBaseItem = None):
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
            if not replacer:
                r = ReplaceItem(left, right)
                self._instructions.append(r)
            else:
                self._instructions.append(replacer(left, right))


class MdBookFixer:
    def __init__(self, path: Union[Path, str, None]):

        if not path:
            self.path = Path(os.getcwd())
        elif isinstance(str, path):
            self.path = Path(path)
        else:
            self.path = path

        self.word_replacer = ReplacerTool(instruction_str=instructions_word_replace)

        self.images = {}
        self.mddocs = {}
        self.links = {}
        self.errors = {}
        self.interactive = True

        if not Path(f"{self.path}/summary.md").exists():
            raise exceptions.Input(f"could not find {self.path}/summary.md")

    def fix(self):

        self.walk(file_methods=self._process_file_load_names)
        self.walk(file_methods=self._fix_file)
        self.errors_write()

    def _fix_content(self, content, path):
        out = ""
        skip = False
        for line in content.split("\n"):
            line2 = line.strip()
            # this will make sure we skip codeblocks
            if line2.startswith("'''") or line2.startswith("```") or line2.startswith('"""'):
                skip = not skip
            if skip:
                out += "%s\n" % line
            else:
                out += "%s\n" % self._fix_line(line, path)
        return out

    def _regex_process(self, regex, line, method, path):
        """
        see if we can find a regex on the line and for wach match run the method

        method is called as method(matched_string,path_object)
        """
        for m in re.finditer(regex, line):
            foundstr = m.string[m.start() : m.end()]
            result = method(foundstr, path)
            line = line.replace(foundstr, result)
        return line

    def _fix_line(self, line, path):
        """
        see what we need to fix on line, all possible regexes are executed

        today support for

        - [a] becomes [a](a.md)
        - links are processed to see if they exist, support for [...](...)  works for images, and markdown docs


        """
        if line and len(line) > 5:
            line = self._replace_word(line)
            # this finds []() in a markdown file
            line = self._regex_process(r"\[[\.\w -\:]*\]$", line, self._fix_link_short, path)
            line = self._regex_process(r"\[[\.\w -\:]*\]\(.+\)", line, self._fix_link, path)
            assert len(line) > 5
        return line

    def error(self, path: Path, msg: str):
        print(" " + Tools.text_replace("- {RED}ERROR:%s{RESET}" % msg))
        relpath_source_file = path.relative_to(self.path)
        shell()
        w
        if relpath_source_file not in self.errors:
            self.errors[relpath_source_file] = []
        self.errors[relpath_source_file].append(msg)

    def errors_write(self):
        out = "## ERRORS\n\n"
        for key, errors in self.errors.items():
            out += f"### {key}\n\n"
            for error in errors:
                out += f" - {error}\n"
            out += "\n"

        Path(f"{self.path}\ERRORS.md").write_text(out)

    def _fix_link_short(self, part, path):
        """
        [something] becomes [something](something.md)
        """
        descr = part.split("(", 1)[0].strip(" []")
        return f"[{descr}]({descr}.md)"

    def _fix_link(self, part: Link, path: Path):
        try:
            link = part.split("(", 1)[1].split(")", 1)[0]
        except:
            shell()
            raise RuntimeError()
        descr = part.split("(", 1)[0].strip(" []")
        link = link.lower().strip()
        relpath_source_file = j.sal.fs.pathRemoveDirPart(path, toremove=self.path)
        if link.startswith("git") or link.startswith("http"):
            # TODO: need to check if git inside so we need to pull the repo
            return part
        else:
            basename = j.sal.fs.getBaseName(link)
            basename = self._name_fix(basename)

        if link.endswith(".md"):
            # its a markdown document
            if not basename in self.mddocs:
                rpath = j.sal.fs.pathRemoveDirPart(path, toremove=self.path)
                self.error(path, f"could not find link {link} in doc {rpath}, the mddoc was not found in this repo.")
                return part
            mddoc_path = self.mddocs[basename]
            mddoc_path_rel = self._link_relative_get(path, mddoc_path)
            self.links[link] = mddoc_path_rel
            part2 = f"[{descr}]({mddoc_path_rel})"
            return part2
        else:
            # is an image
            if not basename in self.images:
                rpath = j.sal.fs.pathRemoveDirPart(path, toremove=self.path)
                self.error(path, f"could not find link {link} in doc {rpath}, the image was not found in this repo.")
                return part
            image_path = self.images[basename]
            image_path_rel = self._link_relative_get(path, image_path)
            self.links[link] = image_path_rel
            part2 = f"[{descr}]({image_path_rel})"
            return part2

        return part

    def _link_relative_get(self, srcdoc_path, link_path):
        link_path_rel = j.sal.fs.pathRemoveDirPart(link_path, toremove=self.path)
        srcdoc_path_rel = j.sal.fs.pathRemoveDirPart(srcdoc_path, toremove=self.path)
        # return link_path_rel
        print(f"link relative get:{srcdoc_path_rel}:{link_path_rel}")
        while True:
            if "/" in link_path_rel and "/" in srcdoc_path_rel:
                a = link_path_rel.split("/", 1)[0]
                b = srcdoc_path_rel.split("/", 1)[0]
                if a == b:
                    # means common pre can be removed
                    link_path_rel = link_path_rel[len(a) + 1 :]
                    srcdoc_path_rel = srcdoc_path_rel[len(b) + 1 :]
                else:
                    break
            else:
                break
        if "/" not in srcdoc_path_rel:
            # means the found link is inside the dir can return as is
            return link_path_rel
        return "../" * srcdoc_path_rel.count("/") + link_path_rel

    def _replace_word(self, part):
        for r in self._replace_list_word:
            part = r.replace(part)
        return part

    def _fix_file(self, path):
        fname = j.sal.fs.getBaseName(path)
        if "." not in fname:
            return
        ext = j.sal.fs.getFileExtension(path)
        if not ext in ["md"]:
            return
        content0 = j.sal.fs.readFile(path)
        content1 = self._fix_content(content0, path=path)
        if content1.strip() != content0.strip():
            Tools.file_write(path, content1)
        return path

    def _name_fix(self, name):
        name = name.replace(" ", "_")
        return j.core.text.strip_to_ascii_dense(name)

    def _path_fix(self, path):
        fname = j.sal.fs.getBaseName(path)
        dname = j.sal.fs.getDirName(path).rstrip("/")
        dpath = "%s/%s" % (dname, self._name_fix(fname))
        if path != dpath:
            j.sal.fs.moveFile(path, dpath)
        return dpath

    def _find_other_files_dir(self, path):
        dname = j.sal.fs.getDirName(path)
        names = [self._name_fix(j.sal.fs.getBaseName(item)) for item in j.sal.fs.listFilesInDir(dname, recursive=False)]
        return names

    def _add_name(self, fname, collection, path, ext):
        while fname in self.images:
            print(f" - found duplicate:{fname} in {path}")
            print(f"    - the duplicate file is: {self.images[fname]}")
            othernames = self._find_other_files_dir(path)
            if self.interactive:
                name_new = Tools.ask_string(
                    f"provide new image name for : {path}\n  only give the name, no extension needed "
                )
            else:
                self.error(f"found duplicate:{fname} in {path}, dupl file is:{self.images[fname]}")
                return path
            if "." in name_new:
                name_new = name_new.split(".")[-1]
            name_new = f"{name_new}.{ext}"
            name_new = self._name_fix(name_new)
            if name_new in othernames or name_new in self.mddocs or name_new in self.images:
                raise exceptions.Input(f"cannot choose this name {name_new}, already exists in the dir {path}")
            # todo: rename file
            dname = j.sal.fs.getDirName(path).rstrip("/")
            path2 = "%s/%s" % (dname, name_new)
            j.sal.fs.moveFile(path, path2)
            path = path2
            fname = name_new
        if fname not in collection:
            collection[fname] = path
        return path

    def _process_file_load_names(self, path):
        ext = j.sal.fs.getFileExtension(path).lower()
        fname = j.sal.fs.getBaseName(path)
        if fname.lower() == "readme.md":
            fname2 = j.sal.fs.getDirName(path, True) + ".md"
            if fname2 not in self._find_other_files_dir(path):
                path2 = "%s/%s" % (j.sal.fs.getDirName(path).rstrip("/"), fname2)
                j.sal.fs.moveFile(path, path2)
                path = path2
            else:
                raise exceptions.Input(f"cannot rename readme.md, because file already exists: {path}")
        if ext in ["jpg", "jpeg", "png"]:
            path = self._add_name(fname, self.images, path, ext)

        elif ext in ["md"]:
            path = self._add_name(fname, self.mddocs, path, ext)

        else:
            print(f" - did not find extension:{path}")
        return path

    def walk(self, path=None, file_methods=[]):
        if not isinstance(file_methods, list):
            file_methods = [file_methods]
        if not path:
            path = self.path
        p = Path(path)
        for dpath in p.iterdir():
            if dpath.name.startswith("."):
                continue
            if dpath.name.startswith("_"):
                continue
            dpath.absolute()
            if dpath.is_dir():
                dpath = dpath.as_posix()
                dpathl = dpath.lower()
                if "/image/" in dpathl or "/images/" in dpathl:
                    self.error(dpath, f"need to replace 'images' to 'img' in {dpathl}")
                self.walk(path=dpath, file_methods=file_methods)
            elif dpath.is_symlink():
                continue
            elif dpath.is_file():
                dpath_posix = dpath.as_posix()
                print(f" - process:{dpath_posix}")
                dpath_posix2 = self._path_fix(dpath_posix)
                assert Tools.exists(dpath_posix2)
                if dpath_posix != dpath_posix2:
                    dpath = Path(dpath_posix2)
                for fm in file_methods:
                    fm(dpath_posix2)
