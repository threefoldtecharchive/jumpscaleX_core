# from core.System import System
from Jumpscale import j
from urllib import parse as urllib_parse

JSBASE = j.baseclasses.object


class TemplateEngine(j.baseclasses.object):
    def __init__(self):
        self.replaceDict = {}  # dict(string,string)
        JSBASE.__init__(self)
        # System ##System

    def add(self, search, replace, variants=False):
        if not j.data.types.string.check(search):
            raise j.exceptions.RuntimeError(
                "only strings can be searched for when using template engine, param search is not a string"
            )
        if not j.data.types.string.check(replace):
            raise j.exceptions.RuntimeError(
                "can only replace with strings when using template engine, param replace is not a string"
            )
        self.replaceDict[search] = replace
        if variants:
            self.replaceDict[search + "s"] = self.makePlural(replace)
            self.replaceDict[self.capitalize(search)] = self.capitalize(replace)
            self.replaceDict[self.capitalize(search + "s")] = self.makePlural(self.capitalize(replace))

    def capitalize(self, txt):
        return txt[0].upper() + txt[1:]

    def makePlural(self, txt):
        if txt[-1] == "y":
            txt = txt[:-1] + "ies"
        else:
            txt = txt + "s"
        return txt

    def __replace(self, body):
        for search in list(self.replaceDict.keys()):
            replace = self.replaceDict[search]
            body = body.replace("{" + search + "}", replace)
            body = body.replace("{:urlencode:" + search + "}", urllib_parse.quote(replace, ""))
        return body

    def replace(self, body, replaceCount=3):
        for i in range(replaceCount):
            body = self.__replace(body)
        return body

    def replaceInsideFile(self, filePath, replaceCount=3):
        self.__createFileFromTemplate(filePath, filePath, replaceCount)

    def writeFileFromTemplate(self, templatePath, targetPath):
        self.__createFileFromTemplate(templatePath, targetPath)

    def getOutputFromTemplate(self, templatePath):
        originalFile = j.sal.fs.readFile(templatePath)
        modifiedString = self.replace(originalFile, replaceCount=3)
        return modifiedString

    def __createFileFromTemplate(self, templatePath, targetPath, replaceCount=3):
        originalFile = j.sal.fs.readFile(templatePath)
        modifiedString = self.replace(originalFile, replaceCount)
        j.sal.fs.writeFile(targetPath, modifiedString)

    def reset(self):
        self.replaceDict = {}


if __name__ == "__main__":
    te = TemplateEngine()
    te.add("login", "kristof")
    te.add("passwd", "root")
    text = "This is a test file for {login} with a passwd:{passwd}"
    print((te.replace(text)))
