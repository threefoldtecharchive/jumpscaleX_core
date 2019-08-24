from Jumpscale import j

def action({{obj.args}}):
    {% if obj.cmdobj.comment != "" %}
    '''
{{obj.comment_indent}}
    '''
    {% endif %}   
{{obj.code_indent}} 


