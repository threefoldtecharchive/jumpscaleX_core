from Jumpscale import j
import tools.codetools.PropertyDef as PropertyDef

JSBASE = j.baseclasses.object


class ClassDef(j.baseclasses.object):
    def __init__(self, filePath, name="", inheritance="", comments=""):
        JSBASE.__init__(self)
        self.filePath = filePath
        self.name = name
        self.comment = comments
        self.inheritanceString = inheritance.strip()
        if self.inheritanceString == "":
            self.inheritedClasses = []
        else:
            self.inheritedClasses = [c.strip() for c in inheritance.split(",")]

        self.docstring = ""
        self.propertyDefs = []
        self.methodDefs = []
        # Will contain a list of dicts, representing instances of the class to be
        # pre-initialized. The dicts contain key/value pairs representing the
        # membername/defaultvalue of the instances.
        self.preinitEntries = []
        self.code = ""  # content of file describing class

    def addPropertyDef(self, prop):
        self.propertyDefs.append(prop)

    def addMethodDef(self, method):
        self.methodDefs.append(method)

    def getProp(self, propname, includeInheritedClasses=False):
        """
        Returns the propertyDef of the property with the given name.
        Returns None if the property could not be found.
        """
        for propdef in self.propertyDefs:
            if propdef.name == propname:
                return propdef
        if includeInheritedClasses:
            for c in self.inheritedClasses:
                classDef = self.codeFile.codeStructure.getClass(c)
                pd = classDef.getProp(propname, True)
                if pd is not None:
                    return pd
        self._log_debug("Could not find the property [%s]" % propname, 3)
        return None
