import os
import fnmatch
from pathlib import Path
from jinja2 import Template


from .Metadata import Metadata


class JSGenerator:
    def __init__(self, j):
        """
        """
        self._j = j
        self._generated = False

    def _check_process_file(self, path):
        bname = os.path.basename(path)
        if bname.startswith("_"):
            return False
        IGNORE = ["/template", "JSLoader.py", "SystemFSDecorators.py", "FixerReplace"]
        for item in IGNORE:
            if path.find(item) != -1:
                return False
        return True

    def lib_link(self, path):
        """
        look for ".jumpscalemodules" and link the parent directory to the JSX lib dir
        :param path:
        :return:
        """
        j = self._j
        # can use j here because will never be used in first step
        for path in j.sal.fs.listFilesInDir(path, True, filter=".jumpscalemodules"):
            dpath = j.sal.fs.getDirName(path)
            target = j.core.tools.text_replace("{DIR_BASE}/lib/jumpscale/%s" % j.sal.fs.getBaseName(dpath))
            j.sal.fs.symlink(dpath, target, True)

    def generate(self, methods_find=False, action_method=None, action_args={}, path=None):
        """
        walk over all found jumpscale libraries
        look for the classes where there is a __jslocation__ inside these are classes which need to be loaded
        :param reset:
        :return:
        """

        self.md = Metadata(self._j)

        # find the directory in which we have all repo's of threefoldtech
        if path:
            rootDir = path
        else:
            rootDir = os.path.dirname(self._j.core.dir_jumpscaleX.rstrip("/"))

        p = Path(rootDir)
        for dpath in p.iterdir():
            if not dpath.is_dir():
                continue
            if dpath.name.startswith("."):
                continue

            for dpath2 in dpath.iterdir():
                jsmodpath = os.path.join(os.fspath(dpath2), ".jumpscalemodules")
                if not os.path.exists(jsmodpath):
                    continue

                js_lib_path = os.path.join(os.fspath(dpath2))

                # NOW WE HAVE FOUND A SET OF JUMPSCALE MODULES
                jumpscale_repo_name = os.path.basename(dpath2)

                for dirName, subdirList, fileList in os.walk(os.fspath(dpath2), followlinks=True):
                    if dirName.find("egg-info") != -1:
                        self._j.shell()
                    if dirName.find("Jumpscale/core") is not -1:
                        continue
                        # skip the core files, they don't need to be read
                    for item in fnmatch.filter(fileList, "*.py"):
                        path = os.path.join(dirName, item)
                        self._log("process", path)
                        if self._check_process_file(path):
                            # self._log("process_ok")
                            jsmodule = self.md.jsmodule_get(
                                path=path, jumpscale_repo_name=jumpscale_repo_name, js_lib_path=js_lib_path
                            )
                            action_args = jsmodule.process(
                                methods_find=methods_find, action_method=action_method, action_args=action_args
                            )

        self.md.groups_load()  # make sure we find all groups

        self._render()
        self.report()

        return action_args

    def _log(self, cat, msg=""):
        print("- %-15s %s" % (cat, msg))
        pass

    def _render(self):

        # create the jumpscale dir if it does not exist yet
        dpath = "%s/jumpscale/" % self._j.dirs.TMPDIR
        if not os.path.exists(dpath):
            os.makedirs(dpath)

        # write the __init__ file otherwise cannot include
        dpath = "%s/jumpscale/__init__.py" % self._j.dirs.TMPDIR
        file = open(dpath, "w")
        file.write("")
        file.close()

        if self._j.application._check_debug():
            template_name = "template_jumpscale_debug.py"
        else:
            template_name = "template_jumpscale.py"
        template_path = os.path.join(os.path.dirname(__file__), "templates", template_name)
        template = Path(template_path).read_text()
        t = Template(template)
        C = t.render(md=self.md)
        dpath = self._j.core.application._lib_generation_path
        file = open(dpath, "w")
        file.write(C)
        file.close()

        self._generated = True

    def report(self):
        """
        kosmos "j.core.jsgenerator.report()"
        write reports to /tmp/jumpscale/code_report.md
        :return:
        """
        if self._generated == False:
            self.generate()
        for name, jsgroup in self.md.jsgroups.items():
            path = "%s/jumpscale/code_report_%s.md" % (self._j.dirs.TMPDIR, jsgroup.name)
            file = open(path, "w")
            file.write(jsgroup.markdown)
            file.close()
        self.report_errors()
        self.report_line_changes()

    def report_errors(self):
        out = ""
        for cat, obj, error, trace in self._j.application.errors_init:
            out += "## %s:%s\n\n" % (cat, obj)
            out += "%s\n\n" % error
            out += "%s\n\n" % trace
        path = "%s/jumpscale/ERRORS_report.md" % (self._j.dirs.TMPDIR)
        file = open(path, "w")
        file.write(out)
        file.close()
        return len(self._j.application.errors_init)

    def report_line_changes(self):
        out = ""
        for item in self.md.line_changes:
            out += str(item)
        path = "%s/jumpscale/LINECHANGES_report.md" % (self._j.dirs.TMPDIR)
        file = open(path, "w")
        file.write(out)
        file.close()
