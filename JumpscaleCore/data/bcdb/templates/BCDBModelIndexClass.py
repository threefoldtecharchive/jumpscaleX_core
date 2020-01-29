

from Jumpscale import j
from Jumpscale.clients.peewee import peewee
import time
import operator
from functools import reduce
from Jumpscale.data.bcdb.BCDBModelIndex import BCDBModelIndex

class {{BASENAME}}(BCDBModelIndex):

    def _sql_index_init(self,**kwargs):
        self._log_info("init index:%s"%self.model.schema.url)

        p = j.clients.peewee

        self.db = self.bcdb.sqlite_index_client
        # print("##DB:%s"%self.db.database)

        class BaseModel(p.Model):
            class Meta:
                # print("*%s"%db)
                database = self.db

        class Index_{{schema.key}}(BaseModel):
            id = p.IntegerField(unique=True)
            nid = p.IntegerField(index=True) #need to store the namespace id
            {%- for field in index.fields %}
            {%- if field.unique %}
            {{field.name}} = p.{{field.type}}(unique=True)
            {%- else %}
            {{field.name}} = p.{{field.type}}(index=True)
            {%- endif %}
            {%- endfor %}

        self.sql = Index_{{schema.key}}
        if j.data.bcdb._master:
            self.sql.create_table(safe=True)

        self._schema_md5_generated = "{{schema._md5}}"

        self.sql_table_name = "index_{{schema.key}}".lower()


    def _sql_index_set(self,obj):
        assert obj.id
        assert obj.nid
        dd={}
        query = [self.sql.id == obj.id]
        {%- for field in index.fields %}
        {%- if field.jumpscaletype.NAME == "numeric" %}
        dd["{{field.name}}"] = obj.{{field.name}}_usd
        query.append((self.sql.{{field.name}} == obj.{{field.name}}_usd))
        {%- elif field.attr %}
        dd["{{field.name}}"] = obj.{{field.attr}}
        query.append((self.sql.{{field.name}} == obj.{{field.attr}}))
        {%- else %}
        dd["{{field.name}}"] = obj.{{field.name}}
        query.append((self.sql.{{field.name}} == obj.{{field.name}}))
        {%- endif %}
        {%- endfor %}
        dd["nid"] = obj.nid

        z = self.sql.get_or_none(id=obj.id)
        if z is None:
            dd["id"] = obj.id
            self.sql.create(**dd)
        else:
            self.sql.update(**dd).where(self.sql.id==obj.id).execute()

        #TODO: if there is other  unique constraint beside ID and we try to force it then
        # the replace function will  delete the row where the constraint is and still update the row
        # where the id points


    def _sql_index_delete(self,obj):
        # if not self.sql.select().where(self.sql.id == obj.id).count()==0:
        self.sql.delete().where(self.sql.id == obj.id).execute()
        if hasattr(obj,"name"):
            self.sql.delete().where(self.sql.name == obj.name).execute()

    def _sql_index_delete_by_id(self,obj_id):
        self.sql.delete().where(self.sql.id == obj_id).execute()


    {%- if index.active_text %}
    def _text_index_set(self,obj):
        {%- for property_name in index.fields_text %}
        val = obj.{{property_name}}
        if val not in ["",None]:
            val=str(val)
            # self._log_debug("key:{{property_name}}:%s:%s"%(val,obj.id))
            self._text_index_set_("{{property_name}}",val,obj.id,nid=obj.nid)
        {%- endfor %}

    def _text_index_delete(self,obj_id=None,nid=None):
        assert obj_id
        assert nid
        {%- for property_name in index.fields_text %}
        self._text_index_delete_("{{property_name}}",obj_id=obj_id,nid=nid)
        {%- endfor %}

    {% else %}
    def _text_index_set(self,obj):
        return

    def _text_index_delete(self,obj):
        return

    {%- endif %}
