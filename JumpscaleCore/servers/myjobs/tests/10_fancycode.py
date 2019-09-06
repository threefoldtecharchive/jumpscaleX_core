import gevent

from Jumpscale import j

import time


def main(self, reset=False):
    """
    kosmos -p 'j.servers.myjobs.test("fancycode")'
    """

    if reset:
        self.reset()

    def testa():
        # NO ARGEMENTS NEEDED

        # we are calling a function which for the test is internal but ofcourse it could have been anywhere
        # normally this function would have been on j..... e.g. a client or sal, ...
        def afunction(llist, bbool, stringA, stringB):
            llist = j.data.types.list.clean(llist)
            bbool = j.data.types.bool.clean(bbool)
            stringIsNone = j.data.types.string.clean(stringA)
            stringNotNone = j.data.types.string.clean(stringB)
            assert isinstance(bbool, bool)
            assert stringIsNone == None
            assert isinstance(stringNotNone, str)
            assert llist == [1, 2, "b"]
            assert bbool == True
            assert stringNotNone == "string"
            return llist

        # see how we can pass different types as string using the replace function
        # this allows us to not have to pass all arguments (which is a lot of repititon)
        # the strings will be converted to the right arguments in the function
        # if we call a function in JS which does not do that conversion then we have to do it in the function ourselves
        return afunction("{alist}", "{abool}", "{astring}", "{astringB}")

    alist = [1, 2, "b"]
    abool = True
    astring = None
    astringB = "string"

    # we're using the local defined arguments to send to the testa method
    # its a nice trick not having to repeat everything
    job1 = self.schedule(testa, args_replace=locals())

    # one worker at least will be started
    self.worker_tmux_start(nr=1)

    gevent.sleep(300)

    job1.wait()

    j.shell()

    print("TEST OK FOR fancy functions")

    # j.application.stop()
