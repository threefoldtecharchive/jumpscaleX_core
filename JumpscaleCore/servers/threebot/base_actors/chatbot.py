import json
from Jumpscale import j


class chatbot(j.baseclasses.threebot_actor):
    """
    """

    def _init(self, **kwargs):
        self.chatbot = self._gedis_server.chatbot

        # check self.chatbot.chatflows for the existing chatflows
        # all required commands are here

    def work_get(self, sessionid, user_session=None):
        """
        ```in
        sessionid = "" (S)
        ```
        """
        res = self.chatbot.session_work_get(sessionid)
        return json.dumps(res)

    def work_report(self, sessionid, result, user_session=None):
        """
        ```in
        sessionid = "" (S)
        result = "" (S)
        ```
        """
        self.chatbot.session_work_set(sessionid, result)
        return

    def session_alive(self, sessionid, schema_out, user_session=None):
        # TODO:*1 check if greenlet is alive
        pass

    def ping(self, user_session=None):
        return "PONG"

    def session_new(self, topic, user_session=None):
        """
        ```in
        topic = "" (S)
        ```
        """
        return json.dumps(self.chatbot.session_new(topic))

    def chatflows_list(self, user_session=None):
        return self.chatbot.chatflows_list()
