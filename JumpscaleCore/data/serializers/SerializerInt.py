from Jumpscale import j

JSBASE = j.baseclasses.object


class SerializerInt(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)

    def dumps(self, obj):
        return str(obj)

    def loads(self, s):
        return int(s)
