import base64
import sys
import uuid
from captcha.image import ImageCaptcha
from importlib import import_module

import json
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
        bot = self.sessions.get(session_id)
        if not bot:
            return {"cat": "md_show", "msg": "Chat has ended", "kwargs": {}}
        elif bot.greenlet.ready():
            self.sessions.pop(session_id)
            msg = "Chat had ended"
            if bot.greenlet.exception:
                j.errorhandler.exception_handle(bot.greenlet.exception, die=False)
                msg = "Something went wrong please contact support"
            return {"cat": "md_show", "msg": msg, "kwargs": {}}
        return bot.q_out.get(block=True)

    def session_work_set(self, session_id, result):
        """
        receives user's answer and set it into `q_in` queue to be consumed afterwards by helper methods
        (ask_string, ask_int, ....) to be able to continue execution
        :param session_id: user session id
        :param result: answer sent by the user
        :return:
        """
        if session_id not in self.sessions:
            return
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

    def chatflows_list(self):
        """
        lists all loaded chatflows
        """
        return list(self.chat_flows.keys())


class Result:
    def __init__(self, loader=str):
        self._value = None
        self._loader = loader

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self._loader(value)


class Form:
    def __init__(self, session):
        self._session = session
        self.messages = []
        self.results = []

    def ask(self):
        self._session.q_out.put({"cat": "form", "msg": self.messages})
        results = j.data.serializers.json.loads(self._session.q_in.get())
        for result, resobject in zip(results, self.results):
            resobject.value = result

    def _append(self, msg, loader=str):
        self.messages.append(msg)
        result = Result()
        self.results.append(result)
        return result

    def string_ask(self, msg, **kwargs):
        return self._append(self._session.string_msg(msg, **kwargs))

    def int_ask(self, msg, **kwargs):
        return self._append(self._session.int_msg(msg, **kwargs), int)

    def secret_ask(self, msg, **kwargs):
        return self._append(self._session.secret_msg(msg, **kwargs))

    def multi_choice(self, msg, options, **kwargs):
        return self._append(self._session.multi_msg(msg, options, **kwargs), j.data.serializers.json.loads)

    def single_choice(self, msg, options, **kwargs):
        return self._append(self._session.single_msg(msg, options, **kwargs))


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
        self.topic_method = topic_method
        self.greenlet = None
        self.launch()

    def launch(self):
        def wrapper():
            try:
                self.topic_method(bot=self)
            except Exception as e:
                j.errorhandler.exception_handle(e, die=False)
                return self.md_show("Something went wrong please contact support")

        self.greenlet = gevent.spawn(wrapper)

    # ###################################
    # Helper methods for asking questions
    # ###################################
    def new_form(self):
        return Form(self)

    def string_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a string answer.
        html generated in the client side will use `<input type="text"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        return self.ask(self.string_msg(msg, **kwargs))

    def string_msg(self, msg, **kwargs):
        return {"cat": "string_ask", "msg": msg, "kwargs": kwargs}

    def secret_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a password answer.
        html generated in the client side will use `<input type="password"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        return self.ask(self.secret_msg(msg, **kwargs))

    def secret_msg(self, msg, **kwargs):
        return {"cat": "secret_ask", "msg": msg, "kwargs": kwargs}

    def text_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a text answer.
        html generated in the client side will use `<textarea></textarea>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        return self.ask(self.text_msg(msg, **kwargs))

    def ask(self, data):
        self.q_out.put(data)
        return self.q_in.get()

    def text_msg(self, msg, **kwargs):
        return {"cat": "text_ask", "msg": msg, "kwargs": kwargs}

    def int_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects an integer answer.
        html generated in the client side will use `<input type="number"/>`
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        return int(self.ask(self.int_msg(msg, **kwargs)))

    def int_msg(self, msg, **kwargs):
        return {"cat": "int_ask", "msg": msg, "kwargs": kwargs}

    def captcha_ask(self, error=False, **kwargs):
        """
        helper method to generate a captcha and verify that the user entered the right answer.
        :param error: if True indicates that the previous captcha attempt failed
        :return: a bool indicating if the user entered the right answer or not
        """
        captcha, message = self.captcha_msg(error, **kwargs)
        return self.ask(message) == captcha

    def captcha_msg(self, error=False, **kwargs):
        image = ImageCaptcha()
        captcha = j.data.idgenerator.generateXCharID(4)
        # this log is for development purposes so we can use the redis client
        self._log_info("generated captcha:%s" % captcha)
        data = image.generate(captcha)
        return (
            captcha,
            {
                "cat": "captcha_ask",
                "captcha": base64.b64encode(data.read()).decode(),
                "msg": "Are you human?",
                "label": "Please enter a valid captcha" if error else "",
                "kwargs": kwargs,
            },
        )

    def location_ask(self, msg, **kwargs):
        """
        helper method to generate a question that expects a `longitude, latitude` string
        html generated in the client side will use openstreetmap div, readonly input field for value.
        :param msg: the question message
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """
        return self.ask(self.location_msg(msg, **kwargs))

    def location_msg(self, msg, **kwargs):
        return {"cat": "location_ask", "msg": msg, "kwargs": kwargs}

    def md_show(self, msg, **kwargs):
        """
        a special helper method to send markdown content to the bot instead of questions.
        usually used for sending info messages to the bot.
        html generated in the client side will use javascript markdown library to convert it
        :param msg: the question message
        :param kwargs: dict of possible extra options like (reset)
        :return:
        """
        return self.ask(self.md_msg(msg, **kwargs))

    def md_msg(self, msg, **kwargs):
        return {"cat": "md_show", "msg": msg, "kwargs": kwargs}

    def md_show_update(self, msg, **kwargs):
        """
        a special helper method to send markdown content to the bot instead of questions.
        usually used for sending info messages to the bot.
        html generated in the client side will use javascript markdown library to convert it
        :param msg: the question message
        :param kwargs: dict of possible extra options like (reset)
        :return:
        """
        message = self.md_msg(msg, **kwargs)
        message["cat"] = "md_show_update"
        self.q_out.put(message)

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
        return j.data.serializers.json.loads(self.ask(self.multi_msg(msg, options, **kwargs)))

    def multi_msg(self, msg, options, **kwargs):
        return {"cat": "multi_choice", "msg": msg, "options": options, "kwargs": kwargs}

    def single_choice(self, msg, options, **kwargs):
        """
        helper method to generate a question that can have single answer from set of choices.
        html generated in the client side will use `<input type="checkbox" name="value" value="${value}">`
        :param msg: the question message
        :param options: list of strings contains the options
        :param kwargs: dict of possible extra options like (validate, reset, ...etc)
        :return: the user answer for the question
        """

        return self.ask(self.single_ms(msg, options, **kwargs))

    def single_msg(self, msg, options, **kwargs):
        return {"cat": "single_choice", "msg": msg, "options": options, "kwargs": kwargs}

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
        return self.ask(self.drop_down_msg(msg, options, **kwargs))

    def drop_down_msg(self, msg, options, **kwargs):
        return {"cat": "drop_down_choice", "msg": msg, "options": options, "kwargs": kwargs}


def test(factory):
    sid = "123"
    factory.session_new("test_chat")
    nr = 0
    while True:
        factory.session_work_get(sid)
        gevent.sleep(1)  # browser is doing something
        nr += 1
        factory.session_work_set(sid, nr)
