from Jumpscale import j


class LoggerFactory(j.baseclasses.object, j.baseclasses.testtools):

    __jslocation__ = "j.tools.logger"
    # _CHILDCLASS = LoggerBase
    # _LoggerInstance = LoggerInstance

    @property
    def debug(self):
        return j.application.debug

    @debug.setter
    def debug(self, value):
        j.application.debug = value

    @property
    def config(self):
        res = {}
        for name in j.core.myenv.config.keys():
            if name.startswith("LOGGER") or name == "DEBUG":
                res[name] = j.core.myenv.config[name]
        return res

    @config.setter
    def config(self, value):
        """

        default :
            {'DEBUG': True,
            'LOGGER_INCLUDE': ['*'],
            'LOGGER_EXCLUDE': ['sal.fs'],
            'LOGGER_LEVEL': 15,
            'LOGGER_CONSOLE': False,
            'LOGGER_REDIS': True
            'LOGGER_REDIS_ADDR': None  #NOT USED YET, std on the core redis
            'LOGGER_REDIS_PORT': None
            'LOGGER_REDIS_SECRET': None
            }

        :param value: dict with config properties, can be all or some of the above
        :return:
        """
        assert j.data.types.dict.check(value)
        changed = False
        for name in j.core.myenv.config.keys():
            if name.startswith("LOGGER") or name == "DEBUG":
                if name in value:
                    if j.core.myenv.config[name] != value[name]:
                        changed = True
                        self._log_debug("changed in config: %s:%s" % (name, value[name]))
                        j.core.myenv.config[name] = value[name]
        if changed:
            j.core.myenv.config_save()
            self.reload()

    def reload(self):
        """
        kosmos 'j.tools.logger.reload()'
        will walk over jsbase classes & reload the logging config
        :return:
        """
        for obj in j.application._iterate_rootobj():
            if hasattr(obj, "_logger_set"):
                obj._logger_set(children=True)
            # self._print(obj._key)

    def test(self, name="base"):
        """
        kosmos 'j.tools.logger.test()'
        """
        self._test_run(name=name)
