import base64
import sys
import uuid
from captcha.image import ImageCaptcha
from importlib import import_module

import json
import gevent
import html
from Jumpscale import j

JSBASE = j.baseclasses.object


class StopChatFlow(Exception):
    def __init__(self, msg=None):
        super().__init__(self, msg)
        self.msg = msg


class GedisChatBotFactory(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.sessions = {}  # all chat sessions
        self.chat_flows = {}  # are the flows to run, code being executed to interact with user

    def session_new(self, topic, query_params=None, **kwargs):
        """
        creates new user session with the specified topic (chatflow)
        :param topic: the topic of chat bot session (chatflow)
        :param kwargs: any extra kwargs that needs to be passed to the session object
                       (i.e. can be used for passing any query parameters)
        :return: created session id
        """
        chatflow = self.chat_flows[topic]()
        self.sessions[chatflow.session_id] = chatflow
        return {"sessionid": chatflow.session_id}

    def session_work_get(self, session_id):
        """
        Blocking method responsible for waiting for new questions added to the queue
        by the chatflow using helper methods (ask_string, ask_integer, ....)
        :param session_id: user session id
        :return: new question dict
        """
        chatflow = self.sessions.get(session_id)
        return chatflow.get_work()

    def session_work_set(self, session_id, result):
        """
        receives user's answer and set it into `q_in` queue to be consumed afterwards by helper methods
        (ask_string, ask_int, ....) to be able to continue execution
        :param session_id: user session id
        :param result: answer sent by the user
        :return:
        """
        chatflow = self.sessions.get(session_id)
        chatflow.set_work(result)

    def session_next_step(self, session_id):
        chatflow = self.sessions.get(session_id)
        chatflow.go_next()
        return

    def session_prev_step(self, session_id, newstep):
        chatflow = self.sessions.get(session_id)
        chatflow.go_back(newstep)
        return


    def chatflows_load(self, chatflows_dir):
        """
        looks for the chat flows exist in `chatflows_dir` to import and load them under self.chat_flows
        :param chatflows_dir: the dir path need to look for chatflows into it
        """    
        files = j.sal.fs.listFilesInDir(chatflows_dir, recursive=True, filter="*.py", followSymlinks=True)
        for chatflow_path in files:
            module, is_changed = j.tools.codeloader.load("chat", path=chatflow_path, reload=False)
            if is_changed:
                module_name = j.sal.fs.getBaseName(chatflow_path)[:-3]
                self.chat_flows[module_name] = module

        return self.chat_flows.keys()

        # for chatflow_path in :
        #     self._log_info("chat:%s" % chatflow_path)
        #     module_name = j.sal.fs.getBaseName(chatflow_path)[:-3]
        #     if module_name.startswith("_"):
        #         continue
            # Each chatflow file must have `chat` method which contains all logic/questions
        #     mod, changed = j.tools.codeloader.load("chat", path=chatflow_path, reload=False)
        #     if changed:
        #         self.chat_flows[module_name] = mod
        #     chatflow_names.append(module_name)
        # return chatflow_names

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

    def ask(self, allow_empty=True):
        valid = False
        while not valid:
            self._session.q_out.put({"cat": "form", "msg": self.messages})
            results = j.data.serializers.json.loads(self._session.q_in.get())
            valid = True
            for result, resobject in zip(results, self.results):
                if not allow_empty and not result:
                    self._session.md_show("You can't input empty values. click next to try again")
                    valid = False
                    break
                resobject.value = result

    def _append(self, msg, loader=str):
        self.messages.append(msg)
        result = Result(loader)
        self.results.append(result)
        return result

    def string_ask(self, msg, **kwargs):
        return self._append(self._session.string_msg(msg, **kwargs))

    def int_ask(self, msg, **kwargs):
        return self._append(self._session.int_msg(msg, **kwargs), int)

    def secret_ask(self, msg, **kwargs):
        return self._append(self._session.secret_msg(msg, **kwargs))

    def download_file(self, msg, filename, **kwargs):
        return self._append(self._session.download_file(msg, filename, **kwargs))

    def multi_list_choice(self, msg, options, **kwargs):
        return self._append(self._session.multi_list_choice(msg, options, **kwargs))

    def datetime_picker(self, msg, **kwargs):
        return self._append(self._session.datetime_picker(msg, **kwargs))

    def upload_file(self, msg, **kwargs):
        return self._append(self._session.upload_file(msg, **kwargs))

    def multi_choice(self, msg, options, **kwargs):
        return self._append(self._session.multi_msg(msg, options, **kwargs), j.data.serializers.json.loads)

    def single_choice(self, msg, options, **kwargs):
        return self._append(self._session.single_msg(msg, options, **kwargs))

    def drop_down_choice(self, msg, options, **kwargs):
        return self._append(self._session.drop_down_msg(msg, options, **kwargs))


class ChatflowFactory(JSBASE):
    __jslocation__ = "j.servers.chatflow"

    def get_class(self):
        return GedisChatBot


class GedisChatBot:
    """
    Contains the basic helper methods for asking questions
    It also have the main queues q_in, q_out that are used to pass questions and answers between browser and server
    """
    steps = []

    def __init__(self, **kwargs):
        """
        :param session_id: user session id created by ChatBotFactory session_new method
        :param topic_method: the bot topic (chatflow)
        :param kwargs: any extra kwargs that is passed while creating the session
                       (i.e. can be used for passing any query parameters)
        """
        self.session_id = str(uuid.uuid4())
        self._state = {}
        self._current_step = 0
        self._greenlet = None
        self._queue_out = gevent.queue.Queue()
        self._queue_in = gevent.queue.Queue()
        self._start()
    
    @property
    def _current_step_state(self):
        return self._state.setdefault(self._current_step, {})

    @property
    def _prev_step_state(self):
        return self._state.get(self._current_step - 1)

    @property
    def first_step(self):
        return self._current_step == 0

    @property
    def last_step(self):
        return self._current_step == len(self.steps) - 1

    def _execute(self, _step_name):
        getattr(self, _step_name)(self._prev_step_state)
        self._queue_out.put({"cat": "next"})

    def _execute_step(self, _step_id):
        _step_name = self.steps[_step_id]
        self._greenlet = gevent.spawn(self._execute, _step_name)
        return True

    def _start(self):
        self._execute_step(self._current_step)

    def go_next(self):
        self._current_step += 1
        return self._execute_step(self._current_step)

    def go_back(self, newstep):
        if newstep:
            self._current_step -= 1
        self._greenlet.kill()
        return self._execute_step(self._current_step)

    def get_work(self):
        return self._queue_out.get()

    def set_work(self, data):
        return self._queue_in.put(data)

    def ask(self, category, message, field=None, **kwargs):
        data = {
            "cat": category, 
            "field": field, 
            "msg": message, 
            "kwargs": {"default": self._current_step_state.get(field) or ""},
            "next": not self.last_step,
            "previous": not self.first_step
        }
        self._queue_out.put(data)
        result = self._queue_in.get()

        if field:
            self._current_step_state[field] = result

    def string_ask(self, msg, field=None, **kwargs):
        return self.ask("string_ask", msg, field, **kwargs)
    
    def secret_ask(self, msg, field=None, **kwargs):
        return self.ask("secret_ask", msg, field, **kwargs)

    def text_ask(self, msg, field=None, **kwargs):
        return self.ask("text_ask", msg, field, **kwargs)

    def int_ask(self, msg, field=None, **kwargs):
        return self.ask("int_ask", msg, field, **kwargs)

    def md_show(self, msg, **kwargs):
        return self.ask("md_show", msg, **kwargs)
        

    # def launch(self):
    #     def wrapper():
    #         try:
    #             self.topic_method(bot=self)
    #         except StopChatFlow as e:
    #             if e.msg:
    #                 self.md_show(e.msg)
    #         except Exception as e:
    #             errmsg = "something went wrong please contact support"
    #             j.errorhandler.exception_handle(e, die=False)
    #             if "message" in dir(e):
    #                 errmsg += f" with error: {e.message}"
    #             return self.md_show(errmsg)

    #     self.greenlet = gevent.spawn(wrapper)

    # ###################################
    # Helper methods for asking questions
    # ###################################
    # def new_form(self):
    #     return Form(self)

    # def stop(self, msg=None):
    #     raise StopChatFlow(msg)


#     def string_msg(self, msg, **kwargs):
#         return {"cat": "string_ask", "msg": msg, "kwargs": kwargs}

#     def secret_ask(self, msg, **kwargs):
#         """
#         helper method to generate a question that expects a password answer.
#         html generated in the client side will use `<input type="password"/>`
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         return self.ask(self.secret_msg(msg, **kwargs))

#     def secret_msg(self, msg, **kwargs):
#         return {"cat": "secret_ask", "msg": msg, "kwargs": kwargs}

#     def download_file(self, msg, filename, **kwargs):
#         return self.ask({"cat": "download_file", "msg": msg, "filename": filename, "kwargs": kwargs})

#     def multi_list_choice(self, msg, options, **kwargs):
#         res = j.data.serializers.json.loads(
#             self.ask({"cat": "multi_list_choice", "msg": msg, "options": options, "kwargs": kwargs})
#         )
#         return list(filter(None, res))

#     def upload_file(self, msg, **kwargs):
#         return self.ask({"cat": "upload_file", "msg": msg, "kwargs": kwargs})

#     def text_ask(self, msg, **kwargs):
#         """
#         helper method to generate a question that expects a text answer.
#         html generated in the client side will use `<textarea></textarea>`
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         return self.ask(self.text_msg(msg, **kwargs))

#     def ask(self, data):
#         self.q_out.put(data)
#         return self.q_in.get()

#     def text_msg(self, msg, **kwargs):
#         return {"cat": "text_ask", "msg": msg, "kwargs": kwargs}

#     def int_ask(self, msg, **kwargs):
#         """
#         helper method to generate a question that expects an integer answer.
#         html generated in the client side will use `<input type="number"/>`
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         return int(self.ask(self.int_msg(msg, **kwargs)))

#     def int_msg(self, msg, **kwargs):
#         return {"cat": "int_ask", "msg": msg, "kwargs": kwargs}

#     def captcha_ask(self, error=False, **kwargs):
#         """
#         helper method to generate a captcha and verify that the user entered the right answer.
#         :param error: if True indicates that the previous captcha attempt failed
#         :return: a bool indicating if the user entered the right answer or not
#         """
#         captcha, message = self.captcha_msg(error, **kwargs)
#         return self.ask(message) == captcha

#     def captcha_msg(self, error=False, **kwargs):
#         image = ImageCaptcha()
#         captcha = j.data.idgenerator.generateXCharID(4)
#         # this log is for development purposes so we can use the redis client
#         self._log_info("generated captcha:%s" % captcha)
#         data = image.generate(captcha)
#         return (
#             captcha,
#             {
#                 "cat": "captcha_ask",
#                 "captcha": base64.b64encode(data.read()).decode(),
#                 "msg": "Are you human?",
#                 "label": "Please enter a valid captcha" if error else "",
#                 "kwargs": kwargs,
#             },
#         )

#     def location_ask(self, msg, **kwargs):
#         """
#         helper method to generate a question that expects a `longitude, latitude` string
#         html generated in the client side will use openstreetmap div, readonly input field for value.
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         return self.ask(self.location_msg(msg, **kwargs))

#     def location_msg(self, msg, **kwargs):
#         return {"cat": "location_ask", "msg": msg, "kwargs": kwargs}

#     def md_show_confirm(self, data, **kwargs):
#         res = "<h1>Please make sure of the entered values before starting deployment</h1>"

#         for key, value in data.items():
#             if value:
#                 res += f"**{key}**: {value}<br>"

#         self.md_show(res)

#     def md_show(self, msg, **kwargs):
#         """
#         a special helper method to send markdown content to the bot instead of questions.
#         usually used for sending info messages to the bot.
#         html generated in the client side will use javascript markdown library to convert it
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (reset)
#         :return:
#         """
#         return self.ask(self.md_msg(msg, **kwargs))

#     def md_msg(self, msg, **kwargs):
#         return {"cat": "md_show", "msg": msg, "kwargs": kwargs}

#     def template_render(self, msg, **kwargs):
#         res = j.tools.jinja2.template_render(text=j.core.text.strip(msg), **kwargs)
#         return self.md_show(res)

#     def md_show_update(self, msg, **kwargs):
#         """
#         a special helper method to send markdown content to the bot instead of questions.
#         usually used for sending info messages to the bot.
#         html generated in the client side will use javascript markdown library to convert it
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (reset)
#         :return:
#         """
#         message = self.md_msg(msg, **kwargs)
#         message["cat"] = "md_show_update"
#         self.q_out.put(message)

#     def loading_show(self, title, wait, **kwargs):
#         load_html = """\
# # Loading {1}...
# <div class="progress">
# <div class="progress-bar active" role="progressbar" aria-valuenow="{0}"
# aria-valuemin="0" aria-valuemax="100" style="width:{0}%">
# {0}%
# </div>
# </div>
# """
#         for x in range(wait):
#             message = self.md_msg(load_html.format((x / wait) * 100, title), **kwargs)
#             message["cat"] = "md_show_update"
#             self.q_out.put(message)
#             gevent.sleep(1)

#     def redirect(self, msg, **kwargs):
#         """
#         a special helper method to redirect the user to a specific url.
#         there is no html generated, It just make use of javascript `window.location` api to redirect the user.
#         :param msg: the url
#         :param kwargs: not used yet
#         :return:
#         """
#         self.q_out.put({"cat": "redirect", "msg": msg, "kwargs": kwargs})
#         # dangerous: better spend time figuring out why this is happening
#         gevent.sleep(1)

#     def html_show(self, msg, **kwargs):
#         """
#         a special helper method to send markdown content to the bot instead of questions.
#         usually used for sending info messages to the bot.
#         html generated in the client side will use javascript markdown library to convert it
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (reset)
#         :return:
#         """
#         html = """\
# # Loading {1}...
#  <div class="progress">
#   <div class="progress-bar active" role="progressbar" aria-valuenow="{0}"
#   aria-valuemin="0" aria-valuemax="100" style="width:{0}%">
#     {0}%
#   </div>
# </div>
# """
#         return html

#     def multi_choice(self, msg, options, **kwargs):
#         """
#         helper method to generate a question that can have multi answers from set of choices.
#         html generated in the client side will use `<input type="checkbox" name="value[]" value="${value}">`
#         :param msg: the question message
#         :param options: list of strings contains the options
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answers for the question
#         """
#         return j.data.serializers.json.loads(self.ask(self.multi_msg(msg, options, **kwargs)))

#     def multi_msg(self, msg, options, **kwargs):
#         return {"cat": "multi_choice", "msg": msg, "options": options, "kwargs": kwargs}

#     def single_choice(self, msg, options, **kwargs):
#         """
#         helper method to generate a question that can have single answer from set of choices.
#         html generated in the client side will use `<input type="checkbox" name="value" value="${value}">`
#         :param msg: the question message
#         :param options: list of strings contains the options
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """

#         return self.ask(self.single_msg(msg, options, **kwargs))

#     def single_msg(self, msg, options, **kwargs):
#         return {"cat": "single_choice", "msg": msg, "options": options, "kwargs": kwargs}

#     def drop_down_choice(self, msg, options, **kwargs):
#         """
#         helper method to generate a question that can have single answer from set of choices.
#         the only difference between this method and `single_choice` is that the html generated in the client side
#         will use `<select> <option value="${value}">${value}</option> ... </select>`
#         :param msg: the question message
#         :param options: list of strings contains the options
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         return self.ask(self.drop_down_msg(msg, options, **kwargs))

#     def drop_down_msg(self, msg, options, **kwargs):
#         return {"cat": "drop_down_choice", "msg": msg, "options": options, "kwargs": kwargs}

#     def drop_down_country(self, msg):
#         return self.drop_down_choice(msg, j.data.countries.names)

#     def autocomplete_drop_down(self, msg, options):
#         return self.drop_down_choice(msg, options, auto_complete=True)

#     def user_info(self, **kwargs):
#         """
#         helper method to retrieve the info of a logged user
#         """
#         self.q_out.put({"cat": "user_info", "kwargs": kwargs})
#         return j.data.serializers.json.loads(self.q_in.get())

#     def qrcode_show(self, data, title=None, msg=None, scale=10, update=False):
#         qr_64 = j.tools.qrcode.base64_get(data, scale=scale)
#         if not title:
#             title = "scan with your application:"
#         content = f"""# {title}

# <p align="center">
# <img src="data:image/png;base64, {qr_64}" alt="qrCode"/>
# </p>
# """
#         if msg:
#             content += f"## {msg}"
#         if update:
#             return self.md_show_update(content)
#         else:
#             return self.md_show(content)

#     def qrcode_show_dict(self, d, title=None, msg=None, scale=10):
#         data = j.data.serializers.json.dumps(d)
#         return self.qrcode_show(data, title, msg, scale=scale)

#     def time_delta_ask(self, msg, allowed_units=None, min="1h", **kwargs):
#         """
#         helper method to generate a question that expects a time delta string(1h, 2m, 3d,...).
#         html generated in the client side will use `<input type="text"/>`
#         :param msg: the question message
#         :param kwargs: dict of possible extra options like (validate, reset, ...etc)
#         :return: the user answer for the question
#         """
#         if not allowed_units:
#             allowed_units = ["h", "d", "w", "M", "Y", "y"]

#         def validate(time_delata_string):
#             if len(time_delata_string) < 2:
#                 return f"Wrong time delta format specified {time_delata_string}. click next to try again"
#             for ch in time_delata_string:
#                 if not ch.isdigit() and ch != ".":
#                     if ch not in allowed_units:
#                         return f"Unit {ch} is not allowed. click next to try again"
#             return None

#         message = """{}
#         Format:
#         hour=h, day=d, week=w, month=M, year=Y
#         I.e. 2 days = 2d
#         """.format(
#             msg
#         )
#         while True:
#             time_delta = self.ask(self.string_msg(message, **kwargs))
#             msg = validate(time_delta)
#             if msg:
#                 self.md_show(msg)
#                 continue

#             try:
#                 delta = j.data.time.getDeltaTime(time_delta)
#             except Exception:
#                 msg = "Wrong time delta format specified please enter a correct one. click next to try again"
#                 self.md_show(msg)
#                 continue
#             if delta < j.data.time.getDeltaTime(min):
#                 msg = f"Wrong time delta. minimum time is {min}. click next to try again"
#                 self.md_show(msg)
#                 continue
#             return delta


# def test(factory):
#     sid = "123"
#     factory.session_new("test_chat")
#     nr = 0
#     while True:
#         factory.session_work_get(sid)
#         gevent.sleep(1)  # browser is doing something
#         nr += 1
#         factory.session_work_set(sid, nr)











#    steps = []
#     def __init__(self):
#         self.id = str(uuid.uuid4())
#         self._state = {}
#         self._current_step = 0
#         self.queue_out = Queue()
#         self.queue_in = Queue()
#         self.start()
#         self.greenlet = None

#     @property
#     def _current_step_state(self):
#         return self._state.setdefault(self._current_step, {})

#     @property
#     def _prev_step_state(self):
#         return self._state.get(self._current_step - 1)

#     def _execute(self, _step_name):
#         getattr(self, _step_name)(self._prev_step_state)
#         self.queue_out.put("next")

#     def _execute_step(self, _step_id):
#         _step_name = self.steps[_step_id]
#         self.greenlet = gevent.spawn(self._execute, _step_name)
#         return True

#     def go_next(self):
#         self._current_step += 1
#         return self._execute_step(self._current_step)

#     def go_back(self):
#         self._current_step -= 1
#         self.greenlet.kill()
#         return self._execute_step(self._current_step)

#     def ask(self, category, field, message, kwargs):
#         value = self._current_step_state.get(field)
#         data = {"category": category, "field": field, "message": message, "kwargs": kwargs, "value": value}
#         self.queue_out.put(data)
#         result = self.queue_in.get()
#         self._current_step_state.update(result)
#         return result
