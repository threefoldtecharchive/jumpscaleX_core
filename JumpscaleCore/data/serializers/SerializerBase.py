from Jumpscale import j

JSBASE = j.baseclasses.object


class SerializerBase(j.baseclasses.object):
    def dump(self, filepath, obj):
        data = self.dumps(obj)
        j.sal.fs.writeFile(filepath, data)

    def load(self, path):
        b = j.sal.fs.readFile(path)
        try:
            r = self.loads(b)
        except Exception as e:
            error = "error:%s\n" % e
            error += "\could not parse:\n%s\n" % b
            error += "\npath:%s\n" % path
            raise j.exceptions.Input(message=error)
        return r


# class SerializerHalt(j.baseclasses.object):
#
#     def __init__(self):
#         JSBASE.__init__(self)
#
#     def dump(self, filepath, obj):
#         raise j.exceptions.Base("should not come here")
#
#     def load(self, path):
#         raise j.exceptions.Base("should not come here")
#
#     def dumps(self, val):
#         raise j.exceptions.Base("should not come here")
#
#     def loads(self, data):
#         raise j.exceptions.Base("should not come here")
