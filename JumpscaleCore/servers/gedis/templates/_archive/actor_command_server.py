from Jumpscale import j

{# generate the properties #}
{% for cmd in obj.data.cmds %}


def {{cmd.name}}(request, **kwargs):
    {% if cmd.comment != "" %}
    '''
    {{cmd.comment}}
    '''
    {% endif %}
    {{cmd.code}}

{% endfor %}


