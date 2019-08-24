from Jumpscale import j

JSBASE = j.baseclasses.object


class PropertyDef(j.baseclasses.object):
    def __init__(
        self,
        classDef,
        name="",
        defaultVal="",
        type="",
        comments="",
        isArray=False,
        isDict=False,
        dictKey="",
        decorators=None,
    ):
        JSBASE.__init__(self)
        if name.startswith("__"):
            self.name = name[2:]
            self.modifier = "property"
        elif name.startswith("_"):
            self.name = name[1:]
            self.modifier = "private"
        else:
            self.name = name
            self.modifier = "normal"

        self.classDef = classDef
        self.defaultVal = defaultVal
        self.type = type
        self.comment = comments
        self.isArray = isArray

        if decorators is None:
            self.decorators = []
        else:
            self.decorators = decorators

        self.foundgetter = False
        self.foundsetter = False
        self.isDict = isDict
        self.dictKey = dictKey
        self.isPrivate = False
        self.isProperty = False
