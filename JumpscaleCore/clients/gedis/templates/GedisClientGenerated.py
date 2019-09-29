from Jumpscale import j
import sys
# JSBASE = j.baseclasses.object

class GedisClientGenerated():

    def __init__(self,client):
        # JSBASE.__init__(self)
        self._client = client
        self._redis = client._redis

    {# generate the actions #}
    {% for name,cmd in obj.cmds.items() %}

    def {{name}}(self{{cmd.args_client}}):
        {% if cmd.comment != "" %}
        '''
{{cmd.comment_indent2}}
        '''
        {% endif %}

        cmd_name = "{{obj.namespace.lower()}}.{{obj.name.lower()}}.{{name}}" #what to use when calling redis
        {% if cmd.schema_in != None %}
        #schema in exists
        schema_in = j.data.schema.get_from_url(url="{{cmd.schema_in.url}}")
        args = schema_in.new()

        {% for prop in cmd.schema_in.properties %}
        args.{{prop.name}} = {{prop.name}}
        {% endfor %}

        id2 = id if not callable(id) else None #if id specified will put in id2 otherwise will be None
        data = j.data.serializers.msgpack.dumps([id2, args._data])
        try:
            res = self._redis.execute_command(cmd_name,data)
        except Exception as e:
            self.handle_error(e,1,cmd_name=cmd_name)

        {% else %}  #is for non schema based

        {% set args = cmd.cmdobj.args if cmd.cmdobj.args else [] %}

        {% if args|length == 0 %}
        try:
            res =  self._redis.execute_command(cmd_name)
        except Exception as e:
            self.handle_error(e,2,cmd_name=cmd_name)

        {% else %}
        # send multi args with no prior knowledge of schema
        try:
            res = self._redis.execute_command(cmd_name, {{ cmd.args_client.lstrip(',')}})
        except Exception as e:
            self.handle_error(e,3)
        {% endif %} #args bigger than []
        {% endif %} #end of test if is schema_in based or not

        {% if cmd.schema_out != None %}
        # print("{{cmd.schema_out.url}}")
        schema_out = j.data.schema.get_from_url(url="{{cmd.schema_out.url}}")
        if isinstance(res, list):
            res2 = list(map(lambda x: schema_out.new(serializeddata=x), res))
        else:
            res2 = schema_out.new(serializeddata=res)
        {% else %}
        res2 = res
        {% endif %}

        return res2


    {% endfor %}


    def handle_error(self, e, source=None,cmd_name=None):
        try:
            logdict = j.data.serializers.json.loads(str(e))
        except Exception:
            logdict = j.core.myenv.exception_handle(e, die=False, stdout=False)

        addr = self._redis.connection_pool.connection_kwargs["host"]
        port = self._redis.connection_pool.connection_kwargs["port"]
        msg = "GEDIS SERVER %s:%s" % (addr,port)
        if cmd_name:
            msg+=" SOURCE METHOD: %s"% cmd_name
        logdict["source"] = msg
 
        # j.core.tools.log2stdout(logdict=logdict, data_show=True)
        j.core.tools.process_logdict_for_handlers(logdict=logdict, iserror=True)

        raise j.exceptions.RemoteException(message=msg, data=logdict, exception=e)
