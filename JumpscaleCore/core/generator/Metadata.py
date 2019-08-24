from .JSGroup import JSGroup
from .JSModule import JSModule
import os


class Metadata:
    def __init__(self, j):
        self._j = j
        self.jsmodules = {}
        self.jsgroups = {}
        self.jsgroup_names = []

    def jsmodule_get(self, path, jumpscale_repo_name, js_lib_path):
        """
        is file = module
        :param name:
        :return:
        """
        if not path in self.jsmodules:
            self.jsmodules[path] = JSModule(
                self, path=path, jumpscale_repo_name=jumpscale_repo_name, js_lib_path=js_lib_path
            )
        return self.jsmodules[path]

    @property
    def jsmodules_list(self):
        return [item[1] for item in self.jsmodules.items()]

    @property
    def line_changes(self):
        res = []
        for module in self.jsmodules.values():
            if module.lines_changed != {}:
                for lc in module.lines_changed.values():
                    res.append(lc)
        return res

    @property
    def syspaths(self):
        """
        paths which need to be available in sys.paths
        :return:
        """
        res = []
        for path, jsmodule in self.jsmodules.items():
            if jsmodule.js_lib_path != "":
                js_lib_path = os.path.dirname(jsmodule.js_lib_path.rstrip("/"))  # get parent
                if not js_lib_path in res:
                    res.append(js_lib_path)
        return res

    def jsgroup_get(self, name):
        if not name in self.jsgroups:
            self.jsgroups[name] = JSGroup(self, name)
        return self.jsgroups[name]

    def groups_load(self, reset=False):
        """
        :return: ["j.clients",
        """
        if reset or self.jsgroup_names == []:
            for key, jsmodule in self.jsmodules.items():
                if jsmodule.jsgroup_name != "":
                    for i in range(len(jsmodule.jsgroup_name)):
                        # add parents
                        parent = jsmodule.jsgroup_name[i]
                        if parent not in self.jsgroup_names:
                            gr = JSGroup(self, name=jsmodule.jsgroup_name[i])
                            if not i:
                                self.jsgroup_names.append(jsmodule.jsgroup_name[i])
                            self.jsgroups[jsmodule.jsgroup_name[i]] = gr
                        else:
                            gr = self.jsgroups[jsmodule.jsgroup_name[i]]

                        # populate children
                        if i:
                            for x in range(len(jsmodule.jsgroup_name)):
                                # if "hamada" in jsmodule.jsgroup_name:
                                #     import ipdb

                                #     ipdb.set_trace()
                                child = JSGroup(self, name=jsmodule.jsgroup_name[x])
                                gr.child_groups.append(child)
                        gr.jsmodules.append(jsmodule)

    @property
    def markdown(self):
        out = "# METADATA\n\n"
        for name, item in self.jsgroups.items():
            out += item.markdown
        return out

    def __repr__(self):
        out = "# METADATA\n\n"
        for name, item in self.jsgroups.items():
            out += str(item)
        return out

    __str__ = __repr__
