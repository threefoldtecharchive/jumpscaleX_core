from Jumpscale import j

from capnp import KjException

{% if root %}
class JSXObject2(j.data.schema._JSXObjectClassRoot):
{% else %}
class JSXObject2(j.data.schema._JSXObjectClassSub):
{% endif %}

    __slots__ = ["id","_model","_capnp_obj_","_deserialized_items","_acl_id","_acl",
                        {% for prop in obj.properties %}"_{{prop.name}}",{% endfor %}]

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
        {% if prop.jumpscaletype.NAME == "dict" %}
        self._changed_deserialized_items=True
        {% endif %}
        if "{{prop.name}}" in self._deserialized_items:
            return self._deserialized_items["{{prop.name}}"]
        else:
            {% if prop.is_primitive %}
            #if a primitive type then it will just be returned immediately from the capnp
            return {{prop.js_typelocation}}.clean(self._capnp_obj_.{{prop.name_camel}})
            {% elif prop.has_jsxobject %}
            v = {{prop.js_typelocation}}.clean(self._capnp_obj_.{{prop.name_camel}},parent=self)
            self._deserialized_items["{{prop.name}}"] = v
            return self._deserialized_items["{{prop.name}}"]
            {% else %}
            v = {{prop.js_typelocation}}.clean(self._capnp_obj_.{{prop.name_camel}})
            self._deserialized_items["{{prop.name}}"] = v
            return self._deserialized_items["{{prop.name}}"]
            {% endif %}

    @{{prop.name}}.setter
    def {{prop.name}}(self,val):
        if self._model and self._model.readonly:
            raise j.exceptions.Input("object readonly, cannot set.\n%s"%self)
        #CLEAN THE OBJ
        {% if prop.has_jsxobject %}
        val = {{prop.js_typelocation}}.clean(val,parent=self)
        {% else %}
        val = {{prop.js_typelocation}}.clean(val)
        {% endif %}
        # self._log_debug("set:{{prop.name}}='%s'"%(val))
        if val != self.{{prop.name}}:
            # self._log_debug("change:{{prop.name}}" + str(val))
            self._deserialized_items["{{prop.name}}"] = val
            self._changed_deserialized_items=True
            {% if prop.is_complex_type %}
            self._deserialized_items["{{prop.name}}"].__changed = True
            {% endif %}
            if self._model:
                self._model._triggers_call(obj=self, action="change", propertyname="{{prop.name}}")
            if self._root._autosave:  #need to check always at lowest level
                self._root.save()
            #TODO: changes in lists & dics are not seen

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
        if self._changed_deserialized_items:
            return True
        {% for prop in obj.properties %}
        {% if prop.is_jsxobject or prop.is_list or prop.is_complex_type %}
        if self.{{prop.name}}._changed:
            return True
        {% endif %}
        {% endfor %}
        return False

    @_changed.setter
    def _changed(self,value):
        assert value==False #only supported mode
        #need to make sure the objects (list(jsxobj) or jsxobj need to set their state to changed)
        {% for prop in obj.properties %}
        {% if prop.is_jsxobject or prop.is_list or prop.is_complex_type %}
        self.{{prop.name}}._changed = False
        {% endif %}
        {% endfor %}
        self._changed_deserialized_items=False

    @property
    def _capnp_obj(self):
        if self._changed is False:
            return self._capnp_obj_

        ddict = self._capnp_obj_.to_dict()

        {% for prop in obj.properties %}
        if "{{prop.name}}" in self._deserialized_items:
            p={{prop.js_typelocation}}
            o=self._deserialized_items["{{prop.name}}"]
            {% if prop.has_jsxobject %}
            data =  p.toData(o,parent=self) #parent is us because prop
            {% else %}
            data =  p.toData(o)
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

    def serialize(self):
        self._capnp_obj
        {% for prop in obj.properties %}
        {% if prop.is_jsxobject or prop.is_list %}
        self.{{prop.name}}.serialize()
        {% endif %}
        {% endfor %}
        self._deserialized_items = {}
        self._changed_deserialized_items=False


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
        {% elif prop.is_list_jsxobject %}
        d["{{prop.name}}"] = {{prop.js_typelocation}}.toHR(self.{{prop.name}},parent=self)
        {% else %}
        d["{{prop.name}}"] = {{prop.js_typelocation}}.toHR(self.{{prop.name}})
        {% endif %}
        {% endfor %}
        if self.id is not None:
            d["id"] = self.id
        for item in exclude:
            if item in d:
                d.pop(item)
        return d

    def _str_get(self, ansi=True):
        out = ""
        if ansi:
            out += "{YELLOW}## %s\n{RESET}" % self._schema.url
        else:
            out += "## %s\n" % self._schema.url
        if self.id:
            if ansi:
                out += "{GREEN}ID: %s\n{RESET}" % self.id
            else:
                out += "id:%s\n" % self.id

        {% for prop in obj.properties %}
        {% if prop.name == "name" %} #main
        if ansi:
            out += " - {YELLOW}{{prop.name_str}}: %s\n{RESET}" % self.name
        else:
            out += " - {{prop.name_str}}: %s\n" % self.name
        {% elif prop.is_jsxobject %} #main
        out+= "\n"+j.core.text.indent(self.{{prop.name}}._str_get(ansi=ansi).rstrip(),4)+"\n"
        {% elif prop.is_list and prop.has_jsxobject%} #main

        {% if prop.has_jsxobject %} # jsxobject
        items = {{prop.js_typelocation}}.toHR(self.{{prop.name}},parent=self)
        {% else %}
        items = {{prop.js_typelocation}}.toHR(self.{{prop.name}})
        {% endif %} #jsxobject

        if items:
            out+= " - {{prop.name_str}}:\n"
            for item in items:
                if isinstance(item, dict):
                    for key, value in item.items():
                        out += "    - {}: {}".format(key, value)
                else:
                    out+= "    - %s\n"%item.rstrip()
        else:
            out+= " - {{prop.name_str}}: []\n"
        {% else %} #main
        out+= " - {{prop.name_str}}: %s\n"%{{prop.js_typelocation}}.toHR(self.{{prop.name}})

        {% endif %}   #main
        {% endfor %}  #all properties
        if ansi:
            out += "{RESET}"
        out = j.core.tools.text_strip(out, replace=True,die_if_args_left=False)
        return out
