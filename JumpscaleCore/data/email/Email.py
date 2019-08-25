import json
from Jumpscale import j
from .Message import Message
from .Sender import Sender
from .utils import get_msg_path, get_json_msg

JSBASE = j.baseclasses.object


class EmailTool(j.baseclasses.object):
    __jslocation__ = "j.tools.email"

    def _get_lastest_keys(self, n=100):
        """
        Gets the latest (n) keys in the the queue

        :return: list

        """
        return j.core.db.lrange("mails.queue", -1 * n, -1)

    def getLast(self, num=100):
        """
        Gets most recent `num` emails

        :return: list
        """

        messages = []
        keys = self._get_lastest_keys()
        for k in keys:
            m = Message(k, j.core.db.hmget("mails", key))
            messages.append(m)

        return messages

    def _pop_key(self, n=1):
        """
        pops the most recent (n) keys in the queue.

        :returns a key
        """
        return j.core.db.lpop("mails.queue", n)

    def pop(self):
        """
        Pops oldest email from the queue.

        :return: Message
        """
        #  we are adding from the right. the oldest is the one on the left.
        k = self._pop_key()  # ts-guid
        msg = get_json_msg(k)  # get message path
        return Message(k, msg)

    def getSender(self, username, password, host="smtp.mandrillapp.com", port=587):
        return Sender.Sender(username, password, host, port)

    def getDefaultSender(self):
        """
        Gets the default configured email sender

        :return: Sender instance
        """
        # BAD SHOULD NOT BE DONE LIKE THIS !

        # cfg = j.data.serializers.yaml.load(j.sal.fs.joinPaths(j.dirs.JSCFGDIR, 'smtp.yaml'))
        # return self.getSender(cfg['username'], cfg['password'], cfg['host'], cfg['port'])
