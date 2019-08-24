class JSGroup:
    """
    e.g. j.tools
    """

    def __init__(self, md, name):

        self._j = md._j
        self.md = md
        self.name = name.lstrip("j.")
        self.jsmodules = []
        self.child_groups = []

        if "." in self.name:
            raise j.exceptions.Base("cannot be . in name for jsgroup")

    # @property
    # def jsmodules(self):
    #     """
    #     e.g. j.clients
    #     """
    #     res=[]
    #     for item in self.md.jsmodules:
    #         if item.name == self.name:
    #             res.append(item)
    #     return res

    @property
    def jdir(self):
        if self.child_groups:
            full_name = "j"
            for group in self.child_groups:
                full_name += "." + group.name
        else:
            full_name = "j.%s" % self.name.lower()
        return full_name

    @property
    def markdown(self):
        out = "# GROUP: %s\n\n" % (self.name)
        for item in self.jsmodules:
            out += item.markdown
        return out

    def __repr__(self):
        return self.markdown

    __str__ = __repr__
