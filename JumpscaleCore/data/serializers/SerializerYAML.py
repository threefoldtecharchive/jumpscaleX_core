import yaml
from collections import OrderedDict
from Jumpscale import j
from .SerializerBase import SerializerBase

testtoml = """
name = 'something'
multiline = '''
    these are multiple lines
    next line
    '''
nr = 87
nr2 = 34.4
"""


# from .PrettyYAMLDumper import PrettyYaml
class SerializerYAML(SerializerBase):
    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
        return yaml.dump(obj, default_flow_style=False, default_style="", indent=4, line_break="\n")

    def loads(self, s):
        # out=cStringIO.StringIO(s)
        try:
            return yaml.load(s)
        except Exception as e:
            error = "error:%s\n" % e
            error += "\nyaml could not parse:\n%s\n" % s
            raise j.exceptions.Input(message=error)

    def load(self, path):
        try:
            s = j.sal.fs.readFile(path)
        except Exception as e:
            error = "error:%s\n" % e
            error += "\npath:%s\n" % path
            raise j.exceptions.Input(message=error)

        try:
            return yaml.load(s)
        except Exception as e:
            error = "error:%s\n" % e
            error += "\nyaml could not parse:\n%s\n" % s
            raise j.exceptions.Input(message=error)

    def ordered_load(self, stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
        """
        load a yaml stream and keep the order
        """

        class OrderedLoader(Loader):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
        return yaml.load(stream, OrderedLoader)

    def ordered_dump(self, data, stream=None, Dumper=yaml.Dumper, **kwds):
        """
        dump a yaml stream with keeping the order
        """

        class OrderedDumper(Dumper):
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return yaml.dump(data, stream, OrderedDumper, **kwds)

    def test(self):
        ddict = j.data.serializers.toml.loads(testtoml)
        # TODO:*3 write some test


# from Jumpscale import j

# from yaml import load, dump
# try:
#     from yaml import CLoader as Loader, CDumper as Dumper
# except ImportError:
#     from yaml import Loader, Dumper


# class YAMLTool:
#     def decode(self,string):
#         """
#         decode yaml string to python object
#         """
#         return load(string)

#     def encode(self,obj,width=120):
#         """
#         encode python (simple) objects to yaml
#         """
#         return dump(obj, width=width, default_flow_style=False)
#
