class JSClass:
    def __init__(self, jsmodule, name):
        self.jsmodule = jsmodule
        self._j = self.jsmodule._j
        self.name = name
        self.imports = []
        self.location = ""
        self.methods = []

    # @property
    # def name(self):
    #     if not self.name.startswith("j."):
    #         raise j.exceptions.Base("name:%s needs to start with j."%self.name)
    #     d= self.name[2:]
    #     d=d[0].upper()+d[1:].lower()
    #     return d

    def method_add(self, nr, method_name):
        self.methods.append((method_name, nr))

    @property
    def importlocation(self):
        """
        :return: e.g. clients.tarantool.TarantoolFactory
        """
        return self.jsmodule.importlocation

    @property
    def jname(self):
        """
        e.g. redis
        """
        return self.location.split(".")[-1]

    @property
    def jdir(self):
        """
        e.g. j.clients
        """
        return ".".join(self.location.split(".")[:-1])

    @property
    def method_names(self):
        return [item[0] for item in self.methods]

    @property
    def markdown(self):
        out = str(self)
        return out

    def __repr__(self):
        out = "\n### CLASS: %s\n\n" % (self.name)
        out += "- location: %s\n" % self.location
        imports = ",".join(self.imports)
        out += "- imports: %s\n" % imports
        mnames = ",".join(self.method_names)
        out += "- methods: %s\n\n" % mnames
        return out

    __str__ = __repr__
