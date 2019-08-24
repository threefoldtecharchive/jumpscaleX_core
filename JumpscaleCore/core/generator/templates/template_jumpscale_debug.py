
# from Jumpscale.core.JSBase import JSBase
import os
import sys
from Jumpscale import j

print ("##DEBUG CODE GENERATION TEMPLATE##")

{% for syspath in md.syspaths %}
if "{{syspath}}" not in sys.path:
    sys.path.append("{{syspath}}")
{%- endfor %}


{% for name, jsgroup in md.jsgroups.items() %}
class group_{{jsgroup.name}}():
    def __init__(self):
        pass

        {% for module in jsgroup.jsmodules %}
        self._{{module.jname}} = None
        {%- endfor %}

    {% for module in jsgroup.jsmodules %}
    @property
    def {{module.jname}}(self):
        if self._{{module.jname}} is None:
            # print("LOAD:{{module.name}}")
            try:
                from {{module.importlocation}} import {{module.name}}
            except Exception as e:
                msg = j.core.application.error_init("import", "{{module.importlocation}}", e)
                return None
            # print("RUN:{{module.name}}")
            try:
                self._{{module.jname}} =  {{module.name}}()
            except Exception as e:
                msg = j.core.application.error_init("execute","{{module.importlocation}}",e,die=False)
                return None
            # print("OK")
        return self._{{module.jname}}

    {%- endfor %}

{{jsgroup.jdir}} = group_{{jsgroup.name}}()

{% endfor %}

{% for name, jsgroup in md.jsgroups.items() %}
{% for module in jsgroup.jsmodules %}
print({{jsgroup.jdir}}.{{module.jname}})
{% endfor %}
{% endfor %}
