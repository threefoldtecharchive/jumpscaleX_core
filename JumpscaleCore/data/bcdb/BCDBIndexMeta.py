from Jumpscale import j

JSBASE = j.baseclasses.object

# THIS IS THE OBJECT USED TO GENERATE THE INDEX CLASS WITH JINJA2


class IndexField:
    def __init__(self, property):
        self.name = property.name
        self.attr = property.attr
        self.jumpscaletype = property.jumpscaletype
        self.unique = property.unique
        if self.jumpscaletype.NAME == "string":
            self.type = "TextField"
        elif self.jumpscaletype.NAME == "enum":
            self.type = "TextField"
        elif self.jumpscaletype.NAME in ["int", "date", "datetime"]:
            self.type = "IntegerField"
        elif self.jumpscaletype.NAME in ["boolean", "bool"]:
            self.type = "BooleanField"
        elif self.jumpscaletype.NAME in ["numeric"]:
            self.type = "FloatField"
        elif self.jumpscaletype.NAME in ["float"]:
            self.type = "FloatField"
        elif self.jumpscaletype.BASETYPE in ["string"]:
            self.type = "TextField"
        else:
            self.type = "UNKNOWN"
            j.shell()
            raise j.exceptions.Base("did not find required type for peewee:%s" % self)

    def __str__(self):
        out = "indexfield:%s:%s:%s" % (self.name, self.type, self.jumpscaletype)
        return out

    __repr__ = __str__


class BCDBIndexMeta(j.baseclasses.object):
    def __init__(self, schema):
        """
        """
        JSBASE.__init__(self)
        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise j.exceptions.Base("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        self.fields = []
        self.fields_key = []
        self.fields_text = []

        for p in schema.properties_index_sql:
            self.fields.append(IndexField(p))

        # for p in schema.properties_index_keys:
        #     self.fields_key.append(p.name)

        for p in schema.properties_index_text:
            self.fields_text.append(p.name)

        self.active = len(self.fields) > 0
        # self.active_keys = len(self.fields_key) > 0
        self.active_text = len(self.fields_text) > 0

    def __str__(self):
        out = "indexmodel:\s"
        for item in self.fields:
            out += " - " + str(item) + "\n"
        return out

    __repr__ = __str__
