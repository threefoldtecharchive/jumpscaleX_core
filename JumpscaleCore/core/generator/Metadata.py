from .JSGroup import JSGroup
from .JSModule import JSModule
import os


class Metadata:
    def __init__(self, j):
        self._j = j
        self.jsmodules = self._j.baseclasses.dict()
        self.jsgroups = None
        self.location_groups = []

    def jsmodule_get(
        self, path, jumpscale_repo_name, js_lib_path, methods_find=True, action_method=None, action_args={}
    ):
        """
        is file = module
        :param name:
        :return:
        """
        m = JSModule(self, path=path, jumpscale_repo_name=jumpscale_repo_name, js_lib_path=js_lib_path)
        action_args = m.process(methods_find=methods_find, action_method=action_method, action_args=action_args)
        if m.location.strip() == "":
            return
        if m.location in self.jsmodules:
            raise RuntimeError("cannot add:%s, location is duplicate '%s'" % (path, m.location))
        self.jsmodules[m.location] = m
        return self.jsmodules[m.location]

    def jsmodules_get_level(self, level=0):
        res = []
        for module in self.jsmodules.values():
            if module.location.count(".") == level:
                res.append(module)
        return res

    @property
    def jsmodules_sorted(self):
        """
        sorst the modules based on nr of . in location
        :return:
        """
        res = []
        for i in range(10):
            r = self.jsmodules_get_level(i)
            if len(r):
                for module in r:
                    if module not in res:
                        res.append(module)
        return res

    def jsgroups_get_level(self, level=0):
        res = []
        for group in self.jsgroups.values():
            if group.location.count(".") == level:
                res.append(group)
        return res

    @property
    def jsgroups_sorted(self):
        """
        sorts the groups based on nr of . in location
        :return:
        """
        res = []
        locations = []
        for i in range(10):
            r = self.jsgroups_get_level(i)
            if len(r):
                for group in r:
                    if group not in res:
                        if group.location_parent not in locations and group.location_parent.find(".") != -1:
                            # means the parent group does not exist yet
                            res.append(JSGroup(self, group.location_parent.strip()))
                        res.append(group)
                        locations.append(group.location)
        return res

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

    # def jsgroup_get(self, name):
    #     if not name in self.jsgroups:
    #         self.jsgroups[name] = JSGroup(self, name)
    #     return self.jsgroups[name]

    def groups_load(self, reset=False):
        """
        :return: ["j.clients",
        """
        if reset or not self.jsgroups:
            self.jsgroups = self._j.baseclasses.dict()
            for key, jsmodule in self.jsmodules.items():
                location_group = jsmodule.location_group
                if location_group not in self.location_groups:
                    # means we need to create a new group
                    self.jsgroups[location_group] = JSGroup(self, location_group)
        return self.jsgroups

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
