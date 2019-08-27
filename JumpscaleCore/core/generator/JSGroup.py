class JSGroup:
    """
    e.g. j.tools
    """

    def __init__(self, md, location):

        self._j = md._j
        self.md = md
        self.location = location
        self._jsmodules = None
        self._children = None

    @property
    def jsmodules(self):
        """
        list of modules which belong to this group
        """
        if not self._jsmodules:
            self._jsmodules = []
            for jsmodule in self.md.jsmodules.values():
                if jsmodule.location_group == self.location:
                    self._jsmodules.append(jsmodule)
        return self._jsmodules

    @property
    def name(self):
        return self.location.replace(".", "__").strip()

    @property
    def name_last(self):
        return self.location.split(".")[-1].strip()

    @property
    def location_parent(self):
        loc = self.location.strip(".")
        r = ".".join(loc.split(".")[:-1])
        return r

    @property
    def children(self):
        """
        list children groups (groups in groups)
        """
        if not self._children:
            self._children = []
            for location, group in self.md.jsgroups.items():
                if self.location.startswith(group.location) and self.location != group.location:
                    t = self.location.replace(group.location, "")  # get the grouplocation out
                    t = t.strip(".")
                    if "." not in t:
                        # means its a direct kid
                        self._children.append(group)
        return self._children

    # @property
    # def jdir(self):
    #     if self.child_groups:
    #         full_name = "j"
    #         for group in self.child_groups:
    #             full_name += "." + group.name
    #     else:
    #         full_name = "j.%s" % self.name.lower()
    #     return full_name

    @property
    def markdown(self):
        out = "# GROUP: %s\n\n" % (self.location)
        if len(self.children) > 0:
            out += "## Children\n\n"
            for jsmodule in self.jsmodules:
                out += "- %s\n" % jsmodule.location
            out += "\n"

        for item in self.jsmodules:
            out += item.markdown
        return out

    def __repr__(self):
        return self.markdown

    __str__ = __repr__
