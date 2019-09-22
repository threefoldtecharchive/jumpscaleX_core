from Jumpscale import j

JSBASE = j.baseclasses.object


class GedisCmd(JSBASE):
    def _init(self, namespace=None, cmd=None):
        """
        these are the cmds which get executed by the gevent server handler for gedis
        (cmds coming from websockets or redis interface)
        """
        assert namespace
        assert cmd

        ## is resulting obj from
        # @url = jumpscale.gedis.cmd
        # name = ""
        # comment = ""
        # schema_in = ""
        # schema_out = ""
        # args = (ls)
        self.cmdobj = cmd

        # self.data = cmd._data
        self.namespace = namespace
        self.name = cmd.name

        if cmd.schema_in_url != "":
            self.schema_in = j.data.schema.get_from_url(url=cmd.schema_in_url)
        else:
            self.schema_in = None

        if cmd.schema_out_url != "":
            self.schema_out = j.data.schema.get_from_url(url=cmd.schema_out_url)
        else:
            self.schema_out = None

        # self._method = None

    @property
    def args(self):
        """
        is text representation of what needs to come in method for the server
        e.g. method(something=...) in between the ()
        """
        if self.schema_in is None:
            return self.cmdobj.args

        out = ""
        for prop in self.schema_in.properties:
            d = prop.default_as_python_code
            out += "%s=%s, " % (prop.name, d)
        out = out.rstrip().rstrip(",").rstrip()
        out += ",schema_out=None, user_session=None"
        return out

    @property
    def args_client(self):
        """


        """
        arguments = [a.strip() for a in self.cmdobj.args]

        if self.schema_in is None:

            if not self.cmdobj.args:
                return ""

            args = self.cmdobj.args

            to_exclude = ["schema_out", ":", "user_session"]
            for item in to_exclude:
                if item in args:
                    args.remove(item)

            if args:
                return "," + ",".join(args)

            return ""
        else:
            if len(self.schema_in.properties) == 0:
                return ""
            else:
                if len(arguments) == 1 and len(self.schema_in.properties) > 1:
                    out = ",id=0,"
                else:
                    out = ","
            for prop in self.schema_in.properties:
                d = prop.default_as_python_code
                out += "%s=%s, " % (prop.name, d)
            out = out.rstrip().rstrip(",").rstrip().rstrip(",")
            return out

    @property
    def args_client_js(self):
        t = self.args_client.strip(",")
        t = t.replace("False", "false")
        t = t.replace("True", "true")
        t = t.replace("**", "...")
        t = t.replace("*", "...")
        if t.strip() == ",schema_out":
            return ""
        return t

    @property
    def code_indent(self):
        return j.core.text.indent(self.cmdobj.code)

    @property
    def comment(self):
        return self.cmdobj.comment

    @property
    def comment_indent(self):
        return j.core.text.indent(self.cmdobj.comment).rstrip()

    @property
    def comment_indent2(self):
        return j.core.text.indent(self.cmdobj.comment, nspaces=8).rstrip()

    # @property
    # def method_generated(self):
    #     """
    #     is a real python method, can be called, here it gets loaded & interpreted
    #     """
    #     if self._method is None:
    #         self._method = j.tools.jinja2.code_python_render(
    #             obj_key="action", path="%s/templates/actor_command_server.py" %
    #             j.servers.gedis.path, obj=self, objForHash=self._data)
    #     return self._method

    def __repr__(self):
        return "%s:%s" % (self.namespace, self.name)

    __str__ = __repr__
