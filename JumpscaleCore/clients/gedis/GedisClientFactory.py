from Jumpscale import j

from .GedisClient import GedisClient

JSConfigBase = j.baseclasses.object_config_collection


class GedisClientCmds:
    def __init__(self, client):
        self._client = client
        self.__dict__.update(client.cmds.__dict__)

    def __str__(self):
        output = "Gedis Client: (instance=%s) (address=%s:%-4s)" % (
            self._client.name,
            self._client.host,
            self._client.port,
        )
        return output

    __repr__ = __str__


class GedisClientFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.gedis"
    _CHILDCLASS = GedisClient

    # def get(self, name="base", host="localhost", port=8901, package_name=None, **kwargs):
    #     """
    #
    #     :param host:
    #     :param port:
    #     :param package_name: needs to be the full name which is $threebotauthor.$packagename
    #     :return:
    #     """
    #
    #     return super().get(name=name, host=host, port=port, package_name=package_name, **kwargs)

    def _handle_error(self, e, source=None, cmd_name=None, redis=None):
        try:
            logdict = j.data.serializers.json.loads(str(e))
        except Exception:
            logdict = j.core.myenv.exception_handle(e, die=False, stdout=False)
        assert redis

        addr = redis._stream.host
        port = redis._stream.port
        msg = "GEDIS SERVER %s:%s" % (addr, port)
        if cmd_name:
            msg += " SOURCE METHOD: %s" % cmd_name
        logdict["source"] = msg

        # j.core.tools.log2stdout(logdict=logdict, data_show=False)
        print(j.core.tools.log2str(logdict, data_show=True, replace=True))
        j.core.tools.process_logdict_for_handlers(logdict=logdict, iserror=True)

        # raise j.exceptions.RemoteException(message=msg, data=logdict, exception=e)
        raise j.exceptions.RemoteException(message=msg)
