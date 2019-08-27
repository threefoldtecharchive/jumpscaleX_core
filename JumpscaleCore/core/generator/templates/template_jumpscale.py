
# from Jumpscale.core.JSBase import JSBase
import os
import sys
from Jumpscale import j

{% for syspath in md.syspaths %}
if "{{syspath}}" not in sys.path:
    sys.path.append("{{syspath}}")
{%- endfor %}

class JSGroup():
    pass

j.core._groups = j.baseclasses.dict()

{% for jsgroup in md.jsgroups_sorted %}
class group_{{jsgroup.name}}(JSGroup):

    def __init__(self):
        pass
        {% for child in jsgroup.children %}
        self._{{child.name}} = None
        {%- endfor %}

        {% for module in jsgroup.jsmodules %}
        self._{{module.jname}} = None
        {%- endfor %}

    {% for child in jsgroup.children %}
    @property
    def {{child.name}}(self):
        if self._{{child.name}} is None:
            self._{{child.name}} =  group_{{child.name}}()
            j.core._groups["{{child.name}}"] = self._{{child.name}}
        return self._{{child.name}}
    {%- endfor %}


    {% for module in jsgroup.jsmodules %}
    @property
    def {{module.jname}}(self):
        if self._{{module.jname}} is None:
            from {{module.importlocation}} import {{module.name}}
            self._{{module.jname}} =  {{module.name}}()
        return self._{{module.jname}}
    {%- endfor %}

{% if "." not in jsgroup.location %}
# if "{{jsgroup.location}}".find("tutorials")!=-1:
#     from pudb import set_trace; set_trace()
{{jsgroup.location}} = group_{{jsgroup.name}}()
j.core._groups["{{jsgroup.name}}"] = {{jsgroup.location}}
{% else %}
{{jsgroup.location_parent}}.__setattr__("{{jsgroup.name_last}}",group_{{jsgroup.name}}())
j.core._groups["{{jsgroup.name}}"] = {{jsgroup.location_parent}}.{{jsgroup.name_last}}
{% endif %}

{% endfor %}

