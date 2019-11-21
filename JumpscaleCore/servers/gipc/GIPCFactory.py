from Jumpscale import j
from .GIPCProcess import GIPCProcess

# import inspect
import gipc


class GIPCFactory(j.baseclasses.object_config_collection, j.baseclasses.testtools):
    """
    GIPC factory
    """

    __jslocation__ = "j.servers.gipc"
    _CHILDCLASS = GIPCProcess

    def _init(self):
        self._last = 0

    def schedule(
        self,
        method,
        name=None,
        inprocess=False,
        # timeout=0,
        # die=True,
        **kwargs,
    ):
        """

        :param method:
        :param timeout:
        :param inprocess:
        :param kwargs:
        :return:
        """
        print("executing method {0} with  and **kwargs {1} ".format(method.__name__, kwargs))
        if inprocess:
            return method(**kwargs)
        if not name:
            self._last += 1
            name = "p%s" % self._last

        p = self.get(name=name)
        p._method = method
        p.kwargs = kwargs
        p.start()
        return p

    def test(self, reset=False):
        """
        kosmos -p 'j.servers.gipc.test()'
        :return:
        """

        def dosomething():
            import time

            time.sleep(5)

        def error_method():
            raise RuntimeError("boem")

        p1 = j.servers.gipc.schedule(dosomething)
        p2 = j.servers.gipc.schedule(error_method)

        error = False
        try:
            p2.wait()
        except Exception as e:
            print("error happened")
            error = True
        assert error

        p1.wait()
        assert p1.state == "OK"
