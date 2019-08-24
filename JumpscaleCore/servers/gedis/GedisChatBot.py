import base64
import sys
import uuid
from captcha.image import ImageCaptcha
from importlib import import_module

import gevent

from Jumpscale import j

JSBASE = j.baseclasses.object


class GedisChatBotFactory(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.sessions = {}  # all chat sessions
        self.chat_flows = {}  # are the flows to run, code being executed to interact with user

    def session_new(self, topic, **kwargs):
        """
        creates new user session with the specified topic (chatflow)
        :param topic: the topic of chat bot session (chatflow)
        :param kwargs: any extra kwargs that needs to be passed to the session object
                       (i.e. can be used for passing any query parameters)
        :return: created session id
        """
        session_id = str(uuid.uuid4())
        topic_method = self.chat_flows[topic]
        session = GedisChatBotSession(session_id, topic_method, **kwargs)
        self.sessions[session_id] = session
        return {"sessionid": session_id}

    def session_work_get(self, session_id):
        """
        Blocking method responsible for waiting for new questions added to the queue
        by the chatflow using helper methods (ask_string, ask_integer, ....)
        :param session_id: user session id
        :return: new question dict
        """
        bot = self.sessions[session_id]
        return bot.q_out.get(block=True)

    def session_work_set(self, session_id, result):
        """
        receives user's answer and set it into `q_in` queue to be consumed afterwards by helper methods
        (ask_string, ask_int, ....) to be able to continue execution
        :param session_id: user session id
        :param result: answer sent by the user
        :return:
        """
        bot = self.sessions[session_id]
        bot.q_in.put(result)
        return

    def chatflows_load(self, chatflows_dir):
        """
        looks for the chat flows exist in `chatflows_dir` to import and load them under self.chat_flows
        :param chatflows_dir: the dir path need to look for chatflows into it
        """
        for chatflow in j.sal.fs.listFilesInDir(chatflows_dir, recursive=True, filter="*.py", followSymlinks=True):
            dir_path = j.sal.fs.getDirName(chatflow)
            if dir_path not in sys.path:
                sys.path.append(dir_path)
            self._log_info("chat:%s" % chatflow)
            module_name = j.sal.fs.getBaseName(chatflow)[:-3]
            if module_name.startswith("_"):
                continue
            loaded_chatflow = import_module(module_name)
            # Each chatflow file must have `chat` method which contains all logic/questions
            self.chat_flows[module_name] = loaded_chatflow.chat


class GedisChatBotSession(JSBASE):
    """
    Contains the basic helper methods for asking questions
    It also have the main queues q_in, q_out that are used to pass questions and answers between browser and server
    """

    def __init__(self, session_id, topic_method, **kwargs):
        """
        :param session_id: user session id created by ChatBotFactory session_new method
        :param topic_method: the bot topic (chatflow)
        :param kwargs: any extra kwargs that is passed while creating the session
                       (i.e. can be used for passing any query parameters)
        """
        JSBASE.__init__(self)
        self.session_id = session_id
        self.q_out = gevent.queue.Queue()  # to browser
        self.q_in = gevent.queue.Queue()  # from browser
        self.kwargs = kwargs
        gevent.spawn(topic_method, bot=self)

    # ###################################
    # Helper methods for asking questions
    # ###################################

    def string_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a string answer.
        html generated in the client side will use `<input type="text"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "string_ask", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def secret_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a password answer.
        html generated in the client side will use `<input type="password"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "secret_ask", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def text_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a text answer.
        html generated in the client side will use `<textarea></textarea>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "text_ask", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def int_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects an integer answer.
        html generated in the client side will use `<input type="number"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "int_ask", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def captcha_ask(self, error=False, **kwargs):
        """
        helper method to generate a captcha and verify that the user entered the right answer.
        :param error: if True indicates that the previous captcha attempt failed
        :return: a bool indicating if the user entered the right answer or not
        """
        image = ImageCaptcha()
        captcha = j.data.idgenerator.generateXCharID(4)
        # this log is for development purposes so we can use the redis client
        self._log_info("generated captcha:%s" % captcha)
        data = image.generate(captcha)
        self.q_out.put(
            {
                "cat": "captcha_ask",
                "captcha": base64.b64encode(data.read()).decode(),
                "msg": "Are you human?",
                "label": "Please enter a valid captcha" if error else "",
                "kwargs": kwargs,
            }
        )
        return self.q_in.get() == captcha

    def location_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a `longitude, latitude` string
        html generated in the client side will use openstreetmap div, readonly input field for value.
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "location_ask", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def md_show(self, msg, **kwargs):
        """
        a special helper method to send markdown content to the bot instead of questions.
        usually used for sending info messages to the bot.
        html generated in the client side will use javascript markdown library to convert it
        :param msg: the question message
        :param kwargs: dict of possible extra options like (reset)
        :return:
        """
        self.q_out.put({"cat": "md_show", "msg": msg, "kwargs": kwargs})
        return self.q_in.get()

    def redirect(self, msg, **kwargs):
        """
        a special helper method to redirect the user to a specific url.
        there is no html generated, It just make use of javascript `window.location` api to redirect the user.
        :param msg: the url
        :param kwargs: not used yet
        :return:
        """
        self.q_out.put({"cat": "redirect", "msg": msg, "kwargs": kwargs})

    def multi_choice(self, msg, options, **kwargs):
        """
        helper method to generate a question that can have multi answers from set of choices.
        html generated in the client side will use `<input type="checkbox" name="value[]" value="${value}">`
        :param msg: the question message
        :param options: list of strings contains the options
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answers for the question
        """
        self.q_out.put({"cat": "multi_choice", "msg": msg, "options": options, "kwargs": kwargs})
        return self.q_in.get()

    def single_choice(self, msg, options, **kwargs):
        """
        helper method to generate a question that can have single answer from set of choices.
        html generated in the client side will use `<input type="checkbox" name="value" value="${value}">`
        :param msg: the question message
        :param options: list of strings contains the options
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """

        self.q_out.put({"cat": "single_choice", "msg": msg, "options": options, "kwargs": kwargs})
        return self.q_in.get()

    def drop_down_choice(self, msg, options, **kwargs):
        """
        helper method to generate a question that can have single answer from set of choices.
        the only difference between this method and `single_choice` is that the html generated in the client side
        will use `<select> <option value="${value}">${value}</option> ... </select>`
        :param msg: the question message
        :param options: list of strings contains the options
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        self.q_out.put({"cat": "drop_down_choice", "msg": msg, "options": options, "kwargs": kwargs})
        return self.q_in.get()


def test(factory):
    sid = "123"
    factory.session_new("test_chat")
    nr = 0
    while True:
        factory.session_work_get(sid)
        gevent.sleep(1)  # browser is doing something
        nr += 1
        factory.session_work_set(sid, nr)
