# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy) 
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j

from Jumpscale.data.bcdb.BCDBModelIndex import BCDBModelIndex

class {{BASENAME}}(BCDBModelIndex):

    {% if index.active %}

    def _sql_index_init(self):
        self._log_info("init index:%s"%self.model.schema.url)

        p = j.clients.peewee

        db = self.bcdb.sqlite_index_client
        # print(db)

        class BaseModel(p.Model):
            class Meta:
                # print("*%s"%db)
                database = db

        class Index_{{schema.key}}(BaseModel):
            id = p.IntegerField(unique=True)
            nid = p.IntegerField(index=True) #need to store the namespace id
            {%- for field in index.fields %}
            {{field.name}} = p.{{field.type}}(index=True)
            {%- endfor %}

        self._sql_index_db = Index_{{schema.key}}
        self._sql_index_db.create_table(safe=True)
        self.sql=self._sql_index_db


    def _sql_index_set(self,obj):
        idict={}
        {%- for field in index.fields %}
        {%- if field.jumpscaletype.NAME == "numeric" %}
        idict["{{field.name}}"] = obj.{{field.name}}_usd
        {%- else %}
        idict["{{field.name}}"] = obj.{{field.name}}
        {%- endif %}
        {%- endfor %}
        assert obj.id
        assert obj.nid
        idict["id"] = obj.id
        idict["nid"] = obj.nid
        #need to delete previous record from index
        self._sql_index_delete(obj)
        self._sql_index_db.insert(**idict).execute()

    def _sql_index_delete(self,obj):
        # if not self._sql_index_db.select().where(self._sql_index_db.id == obj.id).count()==0:
        self._sql_index_db.delete().where(self._sql_index_db.id == obj.id).execute()


    {% else %}
    def _init_index(self):
        return

    def _sql_index_set(self,obj):
        return

    def _sql_index_delete(self,obj):
        return

    def _sql_index_destroy(self, nid=1):
        return

    {% endif %}


    {%- if index.active_keys %}
    def _key_index_set(self,obj):
        {%- for property_name in index.fields_key %}
        val = obj.{{property_name}}
        if val not in ["",None]:
            val=str(val)
            # self._log_debug("key:{{property_name}}:%s:%s"%(val,obj.id))
            self._key_index_set_("{{property_name}}",val,obj.id,nid=obj.nid)
        {%- endfor %}

    def _key_index_delete(self,obj):
        {%- for property_name in index.fields_key %}
        val = obj.{{property_name}}
        if val not in ["",None]:
            val=str(val)
            self._log_debug("delete key:{{property_name}}:%s:%s"%(val,obj.id))
            self._key_index_delete_("{{property_name}}",val,obj.id,nid=obj.nid)
        {%- endfor %}

    {% else %}
    def _key_index_set(self,obj):
        return

    def _key_index_delete(self,obj):
        return

    {%- endif %}

    {%- if index.active_text %}
    def _text_index_set(self,obj):
        {%- for property_name in index.fields_text %}
        val = obj.{{property_name}}
        if val not in ["",None]:
            val=str(val)
            # self._log_debug("key:{{property_name}}:%s:%s"%(val,obj.id))
            self._text_index_set_("{{property_name}}",val,obj.id,nid=obj.nid)
        {%- endfor %}

    def _text_index_delete(self,obj):
        {%- for property_name in index.fields_text %}
        val = obj.{{property_name}}
        if val not in ["",None]:
            val=str(val)
            self._text_index_delete_("{{property_name}}",val,obj.id,nid=obj.nid)
        {%- endfor %}

    {% else %}
    def _text_index_set(self,obj):
        return

    def _text_index_delete(self,obj):
        return

    {%- endif %}







