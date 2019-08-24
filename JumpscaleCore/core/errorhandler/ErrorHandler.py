import sys


class ErrorHandler:
    def __init__(self, j):
        self.__jscorelocation__ = "j.tools.errorhandler"
        self._j = j
        self.exceptions = self._j.core.tools.exceptions
        j.exceptions = self._j.core.tools.exceptions
        self.handlers = self._j.core.myenv.errorhandlers
        self.exception_handle = self._j.core.myenv.exception_handle

    # def try_except_error_process(self, err, die=True):
    #     """
    #     how to use
    #
    #     try:
    #         ##do something
    #     except Exception,e:
    #         j.errorhandler.try_except_error_process(e,die=False) #if you want to continue
    #     """

    # def _error_process(self, err, tb_text=""):
    #     # self._j.shell()
    #     if self._j.application.schemas:
    #         self._j.tools.alerthandler.log(err, tb_text=tb_text)
    #     return err

    # def excepthook(self, ttype, err, tb, die=True):
    #     """ every fatal error in jumpscale or by python itself will result in an exception
    #     in this function the exception is caught.
    #     @ttype : is the description of the error
    #     @tb : can be a python data object or a Event
    #     """
    #     j.shell()
    #     # print ("jumpscale EXCEPTIONHOOK")
    #     if self.inException:
    #         print("**ERROR IN EXCEPTION HANDLING ROUTINES, which causes recursive errorhandling behavior.**")
    #         print(err)
    #         sys.exit(1)
    #         return
    #
    #     if isinstance(err, AttributeError):
    #         err = "{RED}ATTRIBUTE ERROR (prob means cannot find):{RESET} %s" % err
    #
    #     self._j.core.tools.log(msg=err, tb=tb, level=40)
    #     if die:
    #         if self._j.core.myenv.debug:
    #             pudb.post_mortem(tb)
    #         self._j.core.tools.pprint("{RED}CANNOT CONTINUE{RESET}")
    #         sys.exit(1)
    #     else:
    #         print("WARNING IGNORE EXCEPTIONHOOK, NEED TO IMPLEMENT: #TODO:")
    #
    #
    # print(err)
    # tb_text=""
    # if "trace_do" in err.__dict__:
    #     if err.trace_do:
    #         err._trace = self._trace_get(ttype, err, tb)
    #         # err.trace_print()
    #         print(err)
    #         tb_text = err._trace
    # else:
    #     tb_text = self._trace_get(ttype, err, tb)
    #     self._trace_print(tb_text)
    #
    # self.inException = True
    # self._error_process(err, tb_text=tb_text)
    # self.inException = False
    #
    # if die:
    #     sys.exit(1)
