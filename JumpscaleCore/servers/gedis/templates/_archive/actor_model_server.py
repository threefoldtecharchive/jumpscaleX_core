from Jumpscale import j

JSBASE = j.baseclasses.object

SCHEMA = """
{{schema.text}}
"""


class model_{{schema.key}}(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        # self.namespace = "{{model.key}}"
        self.url = "{{schema.url}}"
        self.bcdb = j.data.bcdb.bcdb_instances["{{model.bcdb.name}}"]
        self.model = self.bcdb.models["{{schema.url}}"]
        self.schema = self.model.schema

    def set(self, data_in):
        if self.server_gedis.serializer:
            # e.g. for json
            ddict = self.server_gedis.return_serializer.loads(data_in)
            obj = self.schema.new(datadict=ddict)
            data = self.schema.data
        else:
            id, data = j.data.serializers.msgpack.loads(data_in)

        res = self.model.set(data=data, key=id)
        if res.id is None:
            raise j.exceptions.Base("cannot be None")

        if self.server_gedis.serializer:
            return self.server_gedis.return_serializer.dumps(res.ddict)
        else:
            return j.data.serializers.msgpack.dumps([res.id, res.data])

    def get(self, id):
        id = int(id.decode())
        obj = self.model.get(obj_id=id)
        print("get")
        if self.server_gedis.serializer:
            return self.server_gedis.return_serializer.dumps(obj.ddict)
        else:
            return j.data.serializers.msgpack.dumps([obj.id, obj.data])

    def find(self, total_items_in_page=20, page_number=1, only_fields=[], **args):
        # TODO:*1 what is this, who uses it?
        if isinstance(only_fields, bytes):
            import ast
            only_fields = ast.literal_eval(only_fields.decode())
        return self.model.find(hook=self.hook_get, capnp=True, total_items_in_page=total_items_in_page,
                               page_number=page_number, only_fields=only_fields)

    def new(self):
        return self.model.new()


