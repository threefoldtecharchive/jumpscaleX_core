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

from capnp import KjException

class JSXObject2(j.data.schema._JSXObjectClass):

    __slots__ = ["id","_schema","_model","_autosave","_capnp_obj_","_deserialized_items","_acl_id","_acl",
                        {% for prop in obj.properties %}"_{{prop.name}}",{% endfor %}]

    def _defaults_set(self):
        {% for prop in obj.properties %}
        {% if not prop.is_jsxobject %}
        if {{prop.default_as_python_code}} not in [None,"","0.0",0,'0']:
            self.{{prop.name}} = {{prop.default_as_python_code}}
        {% endif %}
        {% endfor %}
        pass

    {# generate the properties #}
    {% for prop in obj.properties %}
    @property
    def {{prop.name}}(self):
        {% if prop.comment != "" %}
        '''
        {{prop.comment}}
        '''
        {% endif %}

        #this deals with lists and other object types which have customer JSX types
        #if a primitive type then it will just be returned immediately from the capnp
        if "{{prop.name}}" in self._deserialized_items:
            return self._deserialized_items["{{prop.name}}"]
        else:
            {% if prop.has_jsxobject %}
            v = {{prop.js_typelocation}}.clean(self._capnp_obj_.{{prop.name_camel}},model=self._model)
            self._deserialized_items["{{prop.name}}"] = v
            {% else %}
            v = {{prop.js_typelocation}}.clean(self._capnp_obj_.{{prop.name_camel}})
            if isinstance(v,j.data.types._TypeBaseObjClass):
                self._deserialized_items["{{prop.name}}"] = v
            #to make sure that we keep list, json, ... in deserialized items
            elif isinstance({{prop.js_typelocation}},j.data.types._TypeBaseClassUnserialized):
                self._deserialized_items["{{prop.name}}"] = v
            else:
                return v
            {% endif %}
        return self._deserialized_items["{{prop.name}}"]

    @{{prop.name}}.setter
    def {{prop.name}}(self,val):
        if self._model is not None and self._model.readonly:
            raise j.exceptions.Input("object readonly, cannot set.\n%s"%self)
        #CLEAN THE OBJ
        {% if prop.has_jsxobject %}
        val = {{prop.js_typelocation}}.clean(val,model=self._model)
        {% else %}
        val = {{prop.js_typelocation}}.clean(val)
        {% endif %}
        # self._log_debug("set:{{prop.name}}='%s'"%(val))
        if val != self.{{prop.name}}:
            # self._log_debug("change:{{prop.name}}" + str(val))
            self._deserialized_items["{{prop.name}}"] = val
            if self._model:
                self._model._triggers_call(obj=self, action="change", propertyname="{{prop.name}}")
            if self._autosave:
                self.save()

    {% if prop.jumpscaletype.NAME == "numeric" %}
    @property
    def {{prop.name}}_usd(self):
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.name}}._data)

    @property
    def {{prop.name}}_eur(self):
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.name}}._data,curcode="eur")

    def {{prop.name}}_cur(self,curcode):
        """
        @PARAM curcode e.g. usd, eur, egp, ...
        """
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.name}}._data, curcode = curcode)

    {% endif %}

    {% endfor %}


    @property
    def _changed(self):
        changed=False
        {% for prop in obj.properties %}
        {% if prop.has_jsxobject %}
        if self.{{prop.name}}._changed:
            changed = True
        {% else %}
        if "{{prop.name}}" in self._deserialized_items:
            changed = True
        {% endif %}
        {% endfor %}

        return changed

    @_changed.setter
    def _changed(self,value):
        assert value==False #only supported mode
        #need to make sure the objects (list(jsxobj) or jsxobj need to set their state to changed)
        {% for prop in obj.properties %}
        {% if prop.has_jsxobject %}
        self.{{prop.name}}._changed = False
        {% endif %}
        {% endfor %}

    @property
    def _capnp_obj(self):
        if self._changed is False:
            return self._capnp_obj_

        ddict = self._capnp_obj_.to_dict()

        {% for prop in obj.properties %}
        #convert jsxobjects to data data
        if "{{prop.name}}" in self._deserialized_items:
            {% if prop.has_jsxobject %}
            data =  {{prop.js_typelocation}}.toData(self._deserialized_items["{{prop.name}}"],model=self._model)
            {% else %}
            data =  {{prop.js_typelocation}}.toData(self._deserialized_items["{{prop.name}}"])
            {% endif %}
            ddict["{{prop.name_camel}}"] = data
        {% endfor %}


        try:
            self._capnp_obj_ = self._capnp_schema.new_message(**ddict)
        #KjException
        except Exception as e:
            msg="\nERROR: could not create capnp message\n"
            try:
                msg+=j.core.text.indent(j.data.serializers.json.dumps(ddict,sort_keys=True,indent=True),4)+"\n"
            except:
                msg+=j.core.text.indent(str(ddict),4)+"\n"
            msg+="schema:\n"
            msg+=j.core.text.indent(str(self._schema._capnp_schema),4)+"\n"
            msg+="error was:\n%s\n"%e
            raise j.exceptions.Base(msg)

        return self._capnp_obj_


    @property
    def _ddict(self):
        # self._log_debug("DDICT")
        d={}

        {% for prop in obj.properties %}
        {% if prop.is_jsxobject %}
        d["{{prop.name}}"] = self.{{prop.name}}._ddict
        {% else %}
        if isinstance(self.{{prop.name}},j.data.types._TypeBaseObjClass):
            d["{{prop.name}}"] = self.{{prop.name}}._datadict
        else:
            d["{{prop.name}}"] = self.{{prop.name}}
        {% endif %}
        {% endfor %}

        if self.id is not None:
            d["id"]=self.id

        if self._model is not None:
            d=self._model._dict_process_out(d)
        return d

    def _ddict_hr_get(self,exclude=[],ansi=False):
        """
        human readable dict
        """
        d = {}
        {% for prop in obj.properties %}
        {% if prop.is_jsxobject %}
        d["{{prop.name}}"] = self.{{prop.name}}._ddict_hr_get(exclude=exclude)
        {% elif prop.name.endswith("_") %}
        pass
        {% else %}
        if {{prop.js_typelocation}}.NAME in ["list"]:
            res = {{prop.js_typelocation}}.toHR(self.{{prop.name}})
        else:
            res = {{prop.js_typelocation}}.toHR(self.{{prop.name}})
        d["{{prop.name}}"] = res
        {% endif %}
        {% endfor %}
        if self.id is not None:
            d["id"] = self.id
        for item in exclude:
            if item in d:
                d.pop(item)
        return d

    def _str_get(self, ansi=True):
        out = "## "
        if ansi:
            out += "{BLUE}%s\n{RESET}" % self._schema.url_str
        if self.id:
            if ansi:
                out += "{GRAY}id: %s\n{RESET}" % self.id
            else:
                out += "id:%s\n" % self.id
        {% for prop in obj.properties %}
        {% if prop.name == "name" %}
        if ansi:
            out += "{RED}{{prop.name_str}}: %s\n{RESET}" % self.name
        else:
            out += "{{prop.name_str}}: %s\n" % self.name
        {% else %}
        {% if prop.is_jsxobject %}
        out+= j.core.text.indent(self.{{prop.name}}._str_get(ansi=ansi).rstrip(),4)+"\n"
        {% elif prop.is_list %}

        items = {{prop.js_typelocation}}.toHR(self.{{prop.name}})
        if items:
            out+= "{{prop.name_str}}:\n"
            for item in items:
                if isinstance(item, dict):
                    for key, value in item.items():
                        out += "    - {}: {}".format(key, value)
                else:
                    out+= "    - %s\n"%item.rstrip()
        else:
            out+= "{{prop.name_str}}: []\n"
        {% else %}
        out+= "{{prop.name_str}}: %s\n"%{{prop.js_typelocation}}.toHR(self.{{prop.name}})
        {% endif %}
        {% endif %}
        {% endfor %}
        if ansi:
            out += "{RESET}"
        out = j.core.tools.text_strip(out, replace=True,check_no_args_left=False)
        return out








