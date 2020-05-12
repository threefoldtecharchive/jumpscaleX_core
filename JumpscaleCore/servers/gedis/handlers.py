from Jumpscale import j
from redis.exceptions import ConnectionError

from .protocol import RedisCommandParser, RedisResponseWriter
from nacl.signing import VerifyKey
import binascii

JSBASE = j.baseclasses.object

from .UserSession import UserSession, UserSessionAdmin


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


class ResponseWriter:
    """
    ResponseWriter is an object that expose methods
    to write data back to the client
    """

    def __init__(self, socket):
        self._socket = socket
        self._writer = RedisResponseWriter(socket)

    def write(self, value):
        self._writer.encode(value)

    def error(self, value):
        if isinstance(value, dict):
            value = j.data.serializers.json.dumps(value)
        self._writer.error(value)


class GedisSocket:
    """
    GedisSocket encapsulate the raw tcp socket
    when you want to read the next request on the socket,
    call the `read` method, it will return a Request object
    when you want to write back to the client
    call get_writer to get ReponseWriter
    """

    def __init__(self, socket):
        self._socket = socket
        self._parser = RedisCommandParser(socket)
        self._writer = ResponseWriter(self._socket)

    def read(self):
        """
        call this method when you want to process the next request

        :return: return a Request
        :rtype: tuple
        """
        raw_request = self._parser.read_request()
        if not raw_request:
            raise j.exceptions.Value("malformatted request")
        return Request(raw_request)

    @property
    def writer(self):
        return self._writer

    def on_disconnect(self):
        """
        make sur to always call this method before closing the socket
        """
        if self._parser:
            self._parser.on_disconnect()

    @property
    def closed(self):
        return self._socket.closed


class Handler(JSBASE):
    def __init__(self, gedis_server):
        JSBASE.__init__(self)
        self.gedis_server = gedis_server
        self.cmds = {}  # caching of commands
        # will hold classes of type GedisCmds,key is the self.gedis_server._actorkey_get(
        self.cmds_meta = self.gedis_server.cmds_meta

    def handle_gedis(self, socket, address):

        # BUG: if we start a server with kosmos --debug it should get in the debugger but it does not if errors trigger, maybe something in redis?
        # w=self.t
        # raise j.exceptions.Base("d")
        gedis_socket = GedisSocket(socket)

        user_session = UserSessionAdmin()

        try:
            self._handle_gedis_session(gedis_socket, address, user_session=user_session)
        except ConnectionError as e:
            self._log_info("connection closed: %s" % str(e), context="%s:%s" % address)
        except Exception as e:
            self._log_error("unexpected error: %s" % str(e), context="%s:%s" % address, exception=e)
        finally:
            gedis_socket.on_disconnect()
            # self._log_error("connection closed: %s" % str(e), context="%s:%s" % address, exception=e)

    def _handle_gedis_session(self, gedis_socket, address, user_session=None):
        """
        deal with 1 specific session
        :param socket:
        :param address:
        :param parser:
        :param response:
        :return:
        """
        self._log_info("new incoming connection", context="%s:%s" % address)

        while True:
            request = gedis_socket.read()
            self._log_info(f"command {request.command}", context="%s:%s" % address)
            logdict, result = self._handle_request(request, address, user_session=user_session)
            if logdict:
                gedis_socket.writer.error(logdict)
            else:
                gedis_socket.writer.write(result)

    def _authorized(self, cmd_obj, user_session):
        """
        checks if the current session is authorized to access the requested command
        Notes:
        * system actor is always public, it will be used to retrieve the client metadata even before authentication
        * threebot_id should be in the session otherwise it can only access the public methods only
        :return: (True, None) if authorized else (False, reason)
        """

        if user_session.admin:
            return True, None
        elif cmd_obj.rights.public:
            return True, None
        elif not user_session.threebot_id:
            return False, "No user is authenticated on this session and the command isn't public"
        else:
            j.shell()
            w
            # TODO: needs to be reimplemented (despiegk)
            # user = j.data.bcdb.system.user.find(threebot_id=user_session.threebot_id)
            # if not user:
            #     return False, f"Couldn't find user with threebot_id {threebot_id}"
            # return actor_obj.acl.rights_check(userids=[user[0].id], rights=[cmd_name]), None

        return False, "Command not found"

    def _handle_request(self, request, address, user_session):
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
            return None, "OK"
            # TODO: this has not been done properly !!! check Kristof
            tid, seed, signature = request.arguments
            tid = int(tid)

            current_threebot_id = int(j.me.tid)
            # If working on same machine no need to get a client to authenticate
            # otherwise, we'll have infinite loop
            if current_threebot_id != tid:
                try:
                    tclient = j.clients.threebot.client_get(threebot=tid)
                except Exception as e:
                    logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
                    return (logdict, None)
                try:
                    verification = tclient.verify_from_threebot(seed, signature)
                except Exception as e:
                    logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
                    return (logdict, None)

                # if we get here we know that the user has been authenticated properly
                user_session.threebot_id = tclient.tid
                user_session.threebot_name = tclient.name
            else:
                # can't reuse verification methods in 3 bot client, otherwise we gonna go into infinite loop
                # so we verify directly using nacl
                try:
                    VerifyKey(binascii.unhexlify(j.me.encryptor.verify_key_hex)).verify(
                        seed, binascii.unhexlify(signature)
                    )
                except Exception as e:
                    logdict = j.core.myenv.exception_handle(e, die=False, stdout=True)
                    return (logdict, None)
                user_session.threebot_id = tid
                user_session.threebot_name = j.me.name
            return None, "OK"

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

        is_authorized, reason = self._authorized(cmd_obj=cmd, user_session=user_session)
        if not is_authorized:
            not_authorized_err = {
                "message": f"not authorized {reason}",
                "actor_name": request.command.actor,
                "cmd_name": request.command.command,
                "threebot_id": user_session.threebot_id,
            }
            return (j.data.serializers.json.dumps(not_authorized_err), None)

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

        if isinstance(result, list):
            result = [_result_encode(cmd, request.response_type, r) for r in result]
        else:
            result = _result_encode(cmd, request.response_type, result)

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
            return item._json
    else:
        if isinstance(item, j.data.schema._JSXObjectClass):
            if response_type == "json":
                return item._json
            if response_type == "msgpack":
                return item._msgpack
            else:
                return item._data
        return item


# def dm_verify(dm_id, epoch, signed_message):
#     """
#     retrieve the verify key of the threebot identified by bot_id
#     from tfchain
#
#     :param dm_id: threebot identification, can be one of the name or the unique integer
#                     of a threebot
#     :type dm_id: string
#     :param epoch: the epoch param that is signed
#     :type epoch: str
#     :param signed_message: the epoch param signed by the private key
#     :type signed_message: str
#     :return: True if the verification succeeded
#     :rtype: bool
#     :raises: PermissionError in case of wrong message
#     """
#     tfchain = j.clients.tfchain.new("3bot", network_type="TEST")
#     record = tfchain.threebot.record_get(dm_id)
#     verify_key = nacl.signing.VerifyKey(str(record.public_key.hash), encoder=nacl.encoding.HexEncoder)
#     if verify_key.verify(signed_message) != epoch:
#         raise j.exceptions.Permission("You couldn't authenticate your 3bot: {}".format(dm_id))
#
#     return True
