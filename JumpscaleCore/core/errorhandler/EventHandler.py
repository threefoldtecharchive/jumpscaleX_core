class EventHandler:
    def bug_critical(self, msg, source=""):
        """
        will die
        @param e is python error object when doing except
        """
        print("change your code to no longer use j.events...., but raise self._j.exceptions...")
        raise self._j.exceptions.JSBUG(msg, source=source)

    def opserror_critical(self, msg):
        """
        will die
        """
        print("change your code to no longer use j.events...., but raise self._j.exceptions...")
        raise self._j.exceptions.Operations(msg)

    def opserror_warning(self, msg, category=""):
        """
        will NOT die
        """
        self._j.errorhandler.raiseWarning(message=msg, msgpub=msgpub, tags="category:%s" % category, level=level)

    def inputerror_critical(self, msg, category="", msgpub=""):
        """
        will die
        """
        print("change your code to no longer use j.events...., but raise self._j.exceptions...")
        raise self._j.exceptions.Input(msg, tags="category:%s" % category, msgpub=msgpub)

    def inputerror_warning(self, msg, category="", msgpub="", level=5):
        """
        """
        self._j.errorhandler.raiseWarning(message=msg, msgpub=msgpub, tags="category:%s" % category, level=level)
