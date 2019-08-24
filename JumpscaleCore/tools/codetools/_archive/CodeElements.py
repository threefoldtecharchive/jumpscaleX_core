from PropertyDef import PropertyDef
from MethodDef import MethodDef
from ClassDef import ClassDef
from Jumpscale import j

JSBASE = j.baseclasses.object


class CodeElements(j.baseclasses.object):
    def __init__(self, filepath=""):
        JSBASE.__init__(self)
        self.body = ""
        self.classDefs = []
        self.methodDefs = []
        self.license = ""
        self.imports = ""
        self.namespace = ""
        self.types = {}
        self.filepath = filepath
        self.codeStructure = None

    def addClassDef(self, classDef):
        self.classDefs.append(classDef)

    def addMethodDef(self, methodDef):
        self.methodDefs.append(methodDef)

    def getClass(self, classname):
        """
        Returns the classDef of a class with the given name.\
        Returns None if the class can't be found.
        """
        for classDef in self.classDefs:
            if classDef.name == classname:
                return classDef
        self._log_debug("Could not find class [%s]." % classname)
        return None
