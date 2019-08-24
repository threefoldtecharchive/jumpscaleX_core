from Jumpscale import j

JSBASE = j.baseclasses.object


class ClassBase(j.baseclasses.object):
    """
    implement def _obj2dict to overrule serialization, output needs to be dict, reverse is _dict2obj
    """

    # def classCodePrint(self):
    # """
    # print info like source code of class
    # """
    # j.tools.code.classInfoPrint(self)

    # def classCodeEdit(self):
    # """
    # edit this source code in Geany
    # """
    # j.tools.code.classEditGeany(self)

    def __init__(self):
        JSBASE.__init__(self)

    def obj2dict(self):
        return j.tools.code.object2dict(self)

    def dict2obj(self, data):
        j.tools.code.dict2object(self, data)

    def __str__(self):
        return j.tools.code.object2json(self, True)

    __repr__ = __str__


class JSModelBase(ClassBase):
    def __init__(self):
        ClassBase.__init__(self)

    def dict2obj(self, data):
        j.tools.code.dict2JSModelobject(self, data)


class JSRootModelBase(JSModelBase):
    def __init__(self):
        JSModelBase.__init__(self)

    def getMetaInfo(self):
        """
        @return [appname,actorname,modelname,version] if relevant (e.g. for rootobject)
        """
        return self._P__meta
