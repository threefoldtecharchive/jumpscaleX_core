from nacl.encoding import HexEncoder

from Jumpscale import j

from .protocol import Disconnect, Error, ProtocolHandler
from .UserSession import UserSession, UserSessionAdmin

JSBASE = j.baseclasses.object


def _command_split(cmd, author3botname="zerobot", packagename="base"):
    """
    :param cmd: command is in form x.x.x.x split in parts
    :param: author3botname is the default
    :param packagename: is the default packagename
    :return: (author3botname, packagename, actorname, cmd)



    """
    cmd_parts = cmd.split(".")

    if len(cmd_parts) == 4:
        author3botname = cmd_parts[0]
        packagename = cmd_parts[1]
        actor = cmd_parts[2]
        if "__" in actor:
            actor = actor.split("__", 1)[2]
        cmd = cmd_parts[3]
    elif len(cmd_parts) == 3:
        packagename = cmd_parts[0]
        actor = cmd_parts[1]
        if "__" in actor:
            actor = actor.split("__", 1)[1]
        cmd = cmd_parts[2]

    elif len(cmd_parts) == 2:
        actor = cmd_parts[0]
        if "__" in actor:
            actor = actor.split("__", 1)[1]
        cmd = cmd_parts[1]
    elif len(cmd_parts) == 1:
        actor = "system"
        cmd = cmd_parts[0]
    else:
        raise j.exceptions.Base("cmd not properly formatted")

    return author3botname, packagename, actor, cmd


class Command:
    """
    command is an object representing a string gedis command
    it has 4 part
    - author3botname
    - packagename
    - actor
    - command name
    """

    def __init__(self, command):
        self._author3botname, self._packagename, self._actor, self._command = _command_split(command)

    @property
    def author3bot(self):
        return self._author3botname

    @property
    def package(self):
        return self._packagename

    @property
    def actor(self):
        return self._actor

    @property
    def command(self):
        return self._command

    @property
    def key_actor(self):
        return "%s.%s.%s" % (self.author3bot, self.package, self.actor)

    @property
    def key_method(self):
        return "%s.%s.%s.%s" % (self.author3bot, self.package, self.actor, self.command)

    def __str__(self):
        return self.key_method

    __repr__ = __str__


class Request:
    """
    Request is an helper object that
    encapsulate a raw gedis command and expose some property
    for easy access of the different part of the request
    """

    def __init__(self, request):
        self._request_ = request
        self._content_type = None
        self._response_type = None

    @property
    def _request(self):
        return self._request_

    @property
    def command(self):
        """
        return a Command object
        """
        return Command(self._request[0].decode().lower())

    @property
    def arguments(self):
        """
        :return: the list of arguments of any or an emtpy list
        :rtype: list
        """
        if len(self._request) > 1:
            return self._request[1:]
        return []

    @property
    def headers(self):
        """
        :return: return the headers of the request or an emtpy dict
        :rtype: dict
        """
        if len(self._request) > 2:
            # HOW CAN WE KNOW THAT THIS IS JSON???
            try:
                return j.data.serializers.json.loads(self._request[2])
            except:
                # TODO: is not good implementation !!!
                return {}
        return {}

    @property
    def content_type(self):
        """
        :return: read the content type of the request form the headers
        :rtype: string
        """
        if self._content_type:
            return self._content_type
        return self.headers.get("content_type", "auto").casefold()

    @property
    def response_type(self):
        """
        :return: read the response type from the headers
        :rtype: string
        """
        if self._response_type:
            return self._response_type
        return self.headers.get("response_type", "auto").casefold()


class Handler(JSBASE):
    def __init__(self, gedis_server):
        JSBASE.__init__(self)
        self.gedis_server = gedis_server
        self.cmds = {}  # caching of commands
        # will hold classes of type GedisCmds,key is the self.gedis_server._actorkey_get(
        self.cmds_meta = self.gedis_server.cmds_meta
        self._protocol = ProtocolHandler()

    def handle_gedis(self, stream, address=None, client_pub_key=None):
        self._log_info("Connection received: %s:%s" % address)

        user_session = UserSession()
        user_session.public_key = client_pub_key

        # Process client requests until client disconnects.
        while True:
            try:
                data = self._protocol.handle_request(stream)
            except Disconnect:
                self._log_info("Client went away: %s:%s" % address)
                break

            try:
                request = Request(data)
                logdict, resp = self._handle_request(request, address, user_session=user_session)
            except Exception as err:
                resp = Error(err.args[0])

            if logdict:
                resp = Error(logdict)

            self._protocol.write_response(stream, resp)

    def _handle_request(self, request, address=None, user_session=None):
        """
        deal with 1 specific request
        :param request:
        :return: logdict,result
        """

        # process the predefined commands
        if request.command.command == "command":
            return None, "OK"
        elif request.command.command == "ping":
            return None, "PONG"
        elif request.command.command.startswith("config_"):
            if request.command.command == "config_content_type":
                user_session.content_type.value = request.arguments[0].decode()
            elif request.command.command == "config_response_type":
                user_session.response_type.value = request.arguments[0].decode()
            elif request.command.command == "config_format":
                user_session.content_type.value = request.arguments[0].decode()
                user_session.response_type.value = request.arguments[0].decode()
            return None, "OK"
        elif request.command.command == "auth":
            tid, pubkey = request.arguments
            if user_session.public_key.encode(HexEncoder) != pubkey:
                self._log_error("sessions %s failed to authenticate for threebot id %d" % (address, tid))
                return None, False

            user_session.threebot_id = tid
            self._log_info("session %s authenticated for threebot id %d" % (address, tid))
            return None, True

        self._log_debug(
            "command received %s %s %s" % (request.command.author3bot, request.command.actor, request.command.command),
            context="%s:%s" % address,
        )

        # cmd is cmd metadata + cmd.method is what needs to be executed
        try:
            cmd, cmd_method = self._cmd_obj_get(request.command)
            logdict = None
        except Exception as e:
            logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
            return (logdict, None)

        params_list = []
        params_dict = {}
        if cmd.schema_in:

            if user_session.content_type == "json":
                request._content_type = "json"
            elif user_session.content_type == "msgpack":
                request._content_type = "msgpack"

            try:
                params_dict = self._read_input_args_schema(request, cmd)
            except Exception as e:
                logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
                return (logdict, None)
        else:
            params_list = request.arguments

        # the params are binary values now, no conversion happened
        # at this stage the input is in params as a dict

        # makes sure we understand which schema to use to return result from method
        if cmd.schema_out:
            if user_session.content_type == "json":
                request._response_type = "json"
            elif user_session.content_type == "msgpack":
                request._response_type = "msgpack"

            params_dict["schema_out"] = cmd.schema_out

        # now execute the method() of the cmd
        result = None

        self._log_debug("params cmd %s %s" % (params_list, params_dict))
        try:
            # print(f"params_list: {params_list}, params_dict: {params_dict}")
            result = cmd_method(*params_list, user_session=user_session, **params_dict)
            logdict = None
        except Exception as e:
            logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
            return (logdict, None)

        try:
            if isinstance(result, list):
                result = [_result_encode(cmd, request.response_type, r) for r in result]
            else:
                result = _result_encode(cmd, request.response_type, result)
        except Exception as e:
            logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
            return (logdict, None)

        return (logdict, result)

    def _read_input_args_schema(self, request, command):
        """
        get the arguments from an input which is a schema
        :param content_type:
        :param request:
        :param cmd:
        :return:
        """

        def capnp_decode(request, command, die=True):
            try:
                id, data = j.data.serializers.msgpack.loads(request.arguments[0])
            except Exception as e:
                if die:
                    raise j.exceptions.Value(
                        "the content is not valid capnp while you provided content_type=capnp\n%s\n%s"
                        % (e, request.arguments[0])
                    )
                return None

            try:
                # Try capnp which is combination of msgpack of a list of id/capnpdata
                args = command.schema_in.new(serializeddata=data)
                if id:
                    args.id = id
                return args
            except Exception as e:
                if die:
                    raise e
                return None

        def json_decode(request, command, die=True):
            try:
                parsed = j.data.serializers.json.loads(request.arguments[0])
            except:
                if die:
                    raise j.exceptions.Value(
                        "the content is not valid json while you provided content_type=json\n%s\n%s"
                        % (str, request.arguments[0])
                    )
                return None

            try:
                args = command.schema_in.new(datadict=parsed)
                return args
            except Exception as e:
                if die:
                    raise
                return None

        def msgpack_decode(request, command, die=True):
            try:
                parsed = j.data.serializers.msgpack.loads(request.arguments[0])
            except:
                if die:
                    raise j.exceptions.Value(
                        "the content is not valid msgpack while you provided content_type=msgpack\n%s\n%s"
                        % (str, request.arguments[0])
                    )
                return None

            try:
                args = command.schema_in.new(datadict=parsed)
                return args
            except Exception as e:
                if die:
                    raise
                return None

        if request.content_type == "auto":
            args = capnp_decode(request=request, command=command, die=False)
            if args is None:
                args = json_decode(request=request, command=command)
        elif request.content_type == "json":
            args = json_decode(request=request, command=command)
        elif request.content_type == "msgpack":
            args = msgpack_decode(request=request, command=command)
        elif request.content_type == "capnp":
            args = capnp_decode(request=request, command=command)
        else:
            raise j.exceptions.Value("invalid content type was provided the valid types are ['json', 'capnp', 'auto']")

        method_arguments = command.cmdobj.args
        if "schema_out" in method_arguments:
            raise j.exceptions.Base("schema_out should not be in arguments of method")
        if "user_session" in method_arguments:
            raise j.exceptions.Base("user_session should not be in arguments of method")

        params = {}
        for key in command.schema_in.propertynames:
            params[key] = getattr(args, key)

        return params

    def _cmd_obj_get(self, request_cmd):
        """
        arguments come from self._command_split()
        will do caching of the populated command
        :return: the cmd object, cmd.method is the method to be executed
        """

        # caching so we don't have to eval every time
        if request_cmd.key_method in self.cmds:
            return self.cmds[request_cmd.key_method]

        self._log_debug("command cache miss:%s" % request_cmd.key_method)

        actor = j.threebot.actor_get(
            author3bot=request_cmd.author3bot, package_name=request_cmd.package, actor_name=request_cmd.actor
        )

        if request_cmd.key_actor not in self.cmds_meta:
            j.shell()
            raise j.exceptions.Input("Cannot find actor '%s' of geventserver." % request_cmd.key_actor)

        meta = self.cmds_meta[request_cmd.key_actor]

        # check cmd exists in the metadata
        if request_cmd.command not in meta.cmds:
            raise j.exceptions.Input("Cannot find actor method in metadata of geventserver %s" % request_cmd.key_method)

        cmd_obj = meta.cmds[request_cmd.command]

        try:
            cmd_method = getattr(actor, request_cmd.command)
        except Exception as e:
            raise j.exceptions.Input("Could not execute code of method '%s' in gedis server" % request_cmd.key_method)

        self.cmds[request_cmd.key_method] = (cmd_obj, cmd_method)

        return self.cmds[request_cmd.key_method]


def _result_encode(cmd, response_type, item):
    if not item:
        return item

    if cmd.schema_out is not None:
        if response_type == "msgpack":
            return item._msgpack
        elif response_type == "capnp" or response_type == "auto":
            return item._data
        else:
            return j.data.serializers.json.dumps(item._ddict)
            # return item._json
    else:
        if isinstance(item, j.data.schema._JSXObjectClass):
            if response_type == "json":
                return j.data.serializers.json.dumps(item._ddict)
                # return item._json
            if response_type == "msgpack":
                return item._msgpack
            else:
                return item._data
        return item
