from Jumpscale import j

JSBASE = j.baseclasses.object

SCHEMA = """
{{obj.text}}
"""


class model(JSBASE):

    def __init__(self, client):
        JSBASE.__init__(self)
        self.name = "{{obj.name}}"
        self.url = "{{obj.url}}"
        self.schema = j.data.schema.get_from_url(url=self.url)
        self.client = client
        self.redis = client.redis

    def set(self, obj):
        bdata = j.data.serializers.msgpack.dumps([obj.id, obj.data])
        res = self.redis.execute_command("model_%s.set" % self.name, bdata)
        id, _ = j.data.serializers.msgpack.loads(res)
        obj.id = id
        return obj

    def get(self, id):
        res = self.redis.execute_command("model_%s.get" % self.name, str(id))
        id, data = j.data.serializers.msgpack.loads(res)
        obj = self.schema.new(data=data)
        obj.id = id
        return obj

    def find(self, total_items_in_page=20, page_number=1, only_fields=[], {{find_args}}):
        items = self.redis.execute_command("model_%s.find" %
                                           self.name, total_items_in_page, page_number, only_fields, {{kwargs}})
        items = j.data.serializers.msgpack.loads(items)
        result = []

        for item in items:
            id, data = j.data.serializers.msgpack.loads(item)
            obj = self.schema.new(data=data)
            obj.id = id
            result.append(obj)
        return result

    def new(self):
        return self.schema.new()

    def __str__(self):
        return "MODEL%s" % self.url

    __repr__ = __str__


