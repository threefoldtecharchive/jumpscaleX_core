import base64
import sys
import uuid
from captcha.image import ImageCaptcha
from importlib import import_module
import inspect
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
        query_params = html.unescape(query_params)
        query_params = query_params.replace("'", '"')
        try:
            query_params = j.data.serializers.json.loads(query_params)
        except Exception as e:
            self._log_debug(f"parsing query params faild could be empty, {e}")

        kwargs.update(query_params)
        chatflow = self.chat_flows[topic]
        if inspect.isclass(chatflow):
            obj = chatflow(**kwargs)
        else:
            obj = LegacyChatFLow(chatflow, **kwargs)
        
        self.sessions[obj.session_id] = obj
        return {"sessionid": obj.session_id}

    def session_work_get(self, session_id):
        """
        Blocking method responsible for waiting for new questions added to the queue
        by the chatflow using helper methods (ask_string, ask_integer, ....)
        :param session_id: user session id
        :return: new question dict
        """
        chatflow = self.sessions.get(session_id)
        if not chatflow:
            return {"category": "md_show", "msg": "Chat had ended", "kwargs": {}}

        work = chatflow.get_work()
        if work.get("category") == "end":
            self.sessions.pop(session_id)
        
        return work

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
        """Go to next step

        Args:
            session_id (str): session id
        """
        chatflow = self.sessions.get(session_id)
        chatflow.go_next()
        return

    def session_prev_step(self, session_id):
        """Go to previous step

        Args:
            session_id (str): session id
            newstep (bool): if false go to previous question
        """
        chatflow = self.sessions.get(session_id)
        chatflow.go_back()
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
        self.fields = []
        self.results = []

    def ask(self, msg=None):
        self._session.send_data({"category": "form", "msg": msg, "fields": self.fields}, is_slide=True)
        results = j.data.serializers.json.loads(self._session._queue_in.get())
        for result, resobject in zip(results, self.results):
            resobject.value = result

    def _append(self, msg, loader=str):
        self.fields.append(msg)
        result = Result(loader)
        self.results.append(result)
        return result

    def string_ask(self, msg, **kwargs):
        return self._append(self._session.string_msg(msg, **kwargs))

    def int_ask(self, msg, **kwargs):
        return self._append(self._session.int_msg(msg, **kwargs), int)

    def secret_ask(self, msg, **kwargs):
        return self._append(self._session.secret_msg(msg, **kwargs))

    def datetime_picker(self, msg, **kwargs):
        return self._append(self._session.datetime_picker_msg(msg, **kwargs))

    def multi_list_choice(self, msg, options, **kwargs):
        return self._append(self._session.multi_list_choice_msg(msg, options, **kwargs))

    def upload_file(self, msg, **kwargs):
        return self._append(self._session.upload_file_msg(msg, **kwargs))

    def multi_choice(self, msg, options, **kwargs):
        return self._append(self._session.multi_choice_msg(msg, options, **kwargs), j.data.serializers.json.loads)

    def single_choice(self, msg, options, **kwargs):
        return self._append(self._session.single_choice_msg(msg, options, **kwargs))

    def drop_down_choice(self, msg, options, **kwargs):
        return self._append(self._session.drop_down_choice_msg(msg, options, **kwargs))


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
        self.kwargs = kwargs
        self._state = {}
        self._current_step = 0
        self._steps_info = {}
        self._greenlet = None
        self._queue_out = gevent.queue.Queue()
        self._queue_in = gevent.queue.Queue()
        self._start()
    
    @property
    def step_info(self):
        return self._steps_info.setdefault(self._current_step, {"slide": 0})

    @property
    def is_first_slide(self):
        return self.step_info.get("slide", 1) == 1

    @property
    def is_first_step(self):
        return self._current_step == 0

    @property
    def is_last_step(self):
        return self._current_step >= len(self.steps) - 1

    @property
    def info(self):
        previous = True
        if self.is_first_slide:
            if self.is_first_step or not self.step_info.get("previous"):
                previous = False

        return {
            "step": self._current_step + 1,
            "steps": len(self.steps),
            "title": self.step_info.get("title"),
            "previous": previous,
            "last_step": self.is_last_step,
            "first_step": self.is_first_step,
            "first_slide": self.is_first_slide,
            "slide": self.step_info.get("slide", 1)
        }

    def _execute_current_step(self, spawn=True):
        def wrapper(step_name):
            internal_error = False
            try:
                getattr(self, step_name)()
            except StopChatFlow as e:
                if e.msg:
                    self.send_error(e.msg)

            except Exception as e:
                internal_error = True
                j.errorhandler.exception_handle(e, die=False)
                self.send_error("Something wrong happened, please contact support")
            
            if not internal_error:
                if self.is_last_step:
                    self.send_data({"category": "end"})
                else:
                    self._current_step += 1
                    self._execute_current_step(spawn=False)
          
        step_name = self.steps[self._current_step]
        self.step_info["slide"] = 0

        if spawn:
            self._greenlet = gevent.spawn(wrapper, step_name)
        else:
            wrapper(step_name)


    def _start(self):
        self._execute_current_step()

    def go_next(self):
        self._current_step += 1
        self._execute_current_step()

    def go_back(self):
        if self.is_first_slide:
            if self.is_first_step:
                return
            else:
                self._current_step -= 1

        self._greenlet.kill()
        return self._execute_current_step()

    def get_work(self):
        return self._queue_out.get()

    def set_work(self, data):
        return self._queue_in.put(data)

    def send_data(self, data, is_slide=False):
        if is_slide:
            self.step_info["slide"] += 1

        data.setdefault("kwargs", {})
        output = {"info": self.info, "payload": data} 
        self._queue_out.put(output)

    def send_error(self, message, **kwargs):
        self.send_data({
            "category": "error",
            "msg": message,
            "kwargs": kwargs
        })
        self._queue_in.get()

    def ask(self, data):
        self.send_data(data, is_slide=True)
        return self._queue_in.get()

    def user_info(self, **kwargs):
        self.send_data({"category": "user_info", "kwargs": kwargs})
        result = j.data.serializers.json.loads(self._queue_in.get())
        return result

    def string_msg(self, msg, **kwargs):
        return {"category": "string_ask", "msg": msg, "kwargs": kwargs}

    def string_ask(self, msg, **kwargs):
        """Ask for a string value

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            min_length (int): min length
            max_length (int): max length

        Returns:
            str: user input
        """
        return self.ask(self.string_msg(msg, **kwargs))

    def secret_msg(self, msg, **kwargs):
        return {"category": "secret_ask", "msg": msg, "kwargs": kwargs}
    
    def secret_ask(self, msg, **kwargs):
        """Ask for a secret value

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            min_length (int): min length 
            max_length (int): max length

        Returns:
            str: user input
        """
        return self.ask(self.secret_msg(msg, **kwargs))

    def int_msg(self, msg, **kwargs):
        return {"category": "int_ask", "msg": msg, "kwargs": kwargs}

    def int_ask(self, msg, **kwargs):
        """Ask for a inegert value

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            min (int): min value
            max (int): max value

        Returns:
            str: user input
        """
        result = self.ask(self.int_msg(msg, **kwargs))
        if result:
            return int(result)
    
    def text_msg(self, msg, **kwargs):
        return {"category": "text_ask", "msg": msg, "kwargs": kwargs}

    def text_ask(self, msg, **kwargs):
        """Ask for a multi line string value

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
 
        Returns:
            str: user input
        """
        return self.ask(self.text_msg(msg, **kwargs))

    def single_choice_msg(self, msg, options, **kwargs):
        return {"category": "single_choice", "msg": msg, "options": options, "kwargs": kwargs}
    
    def single_choice(self, msg, options, **kwargs):
        """Ask for a single option

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
 
        Returns:
            str: user input
        """
        return self.ask(self.single_choice_msg(msg, options, **kwargs))

    def multi_choice_msg(self, msg, options, **kwargs):
        return {"category": "multi_choice", "msg": msg, "options": options, "kwargs": kwargs}

    def multi_choice(self, msg, options, **kwargs):
        """Ask for a multiple options

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            min_options (int): min number of selected options
            max_options (int): max number selected options

        Returns:
            str: user input
        """
        result = self.ask(self.multi_choice_msg(msg, options, **kwargs))
        return j.data.serializers.json.loads(result)

    def multi_list_choice_msg(self, msg, options, **kwargs):
        return {"category": "multi_list_choice", "msg": msg, "options": options, "kwargs": kwargs}

    def multi_list_choice(self, msg, options, **kwargs):
        """Ask for a multiple options

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            min_options (int): min number of selected options
            max_options (int): max number selected options

        Returns:
            str: user input
        """
        result = self.ask(self.multi_choice_msg(msg, options, **kwargs))
        return j.data.serializers.json.loads(result)

    def drop_down_choice_msg(self, msg, options, **kwargs):
        return {"category": "drop_down_choice", "msg": msg, "options": options, "kwargs": kwargs}

    def drop_down_choice(self, msg, options, **kwargs):
        """Ask for a single options using dropdown

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html

        Returns:
            str: user input
        """
        return self.ask(self.drop_down_choice_msg(msg, options, **kwargs))

    def autocomplete_drop_down(self, msg, options, **kwargs):
        """Ask for a single options using dropdown with auto completion

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html

        Returns:
            str: user input
        """
        return self.drop_down_choice(msg, options, auto_complete=True, **kwargs)

    def datetime_picker_msg(self, msg, **kwargs):        
        return {"category": "datetime_picker", "msg": msg, "kwargs": kwargs}

    def datetime_picker(self, msg, **kwargs):
        """Ask for a datetime

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html

        Returns:
            int: timestamp
        """
        result = self.ask(self.datetime_picker_msg(msg, **kwargs))
        if result:
            return int(result)

    def time_delta_msg(self, msg, **kwargs):
        return {"category": "time_delta", "msg": msg, "kwargs": kwargs}
        
    def time_delta_ask(self, msg, **kwargs):
        """Ask for a time delta example: 1Y 1M 1w 2d 1h

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html

        Returns:
            datetime.datetime: user input
        """
        result =  self.ask(self.time_delta_msg(msg, timedelta=True, **kwargs))
        return j.data.time.getDeltaTime(result)

    def location_msg(self, msg, **kwargs):
        return {"category": "location_ask", "msg": msg, "kwargs": kwargs}
    
    def location_ask(self, msg, **kwargs):
        """Ask for a location [lng, lat]

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html

        Returns:
            list: list([lat, lng])
        """
        result = self.ask(self.location_msg(msg, **kwargs))
        return j.data.serializers.json.loads(result)

    def download_file(self, msg, data, filename, **kwargs):
        """Add a download button to download data as a file

        Args:
            msg (str): message text
            data (str): the data to be in the file
            filename (str): file name
        
        Keyword Arguments:
            md (bool): render message as markdown
            html (bool): render message as html
            
        """
        self.ask({"category": "download_file", "msg": msg, "data": data, "filename": filename, "kwargs": kwargs})

    def upload_file_msg(self, msg, **kwargs):
        return {"category": "upload_file", "msg": msg, "kwargs": kwargs}

    def upload_file(self, msg, **kwargs):
        """Ask for a file to be uploaded

        Args:
            msg (str): message text
        
        Keyword Arguments:
            required (bool): flag to make this field required
            md (bool): render message as markdown
            html (bool): render message as html
            max_size (int): file max size
            allowed_types: list of allowed types example : ['text/plain']

        Returns:
            str: file content
        """
        return self.ask(self.upload_file_msg(msg, ** kwargs))

    def qrcode_show(self, msg, data, scale=10, **kwargs):
        """Show QR code as an image

        Args:
            msg (str): message
            data (str): data to be encoded
            scale (int, optional): qrcode scale. Defaults to 10.

        Keyword Arguments:
            md (bool): render message as markdown
            html (bool): render message as html
        """
        qrcode = j.tools.qrcode.base64_get(data, scale=scale)
        self.send_data({"category": "qrcode_show", "msg": msg, "qrcode": qrcode, "kwargs": kwargs}, is_slide=True)
        self._queue_in.get()

    def captcha_msg(self, **kwargs):
        image = ImageCaptcha()
        captcha = j.data.idgenerator.generateXCharID(4)
        data = image.generate(captcha)
        kwargs["value"] = captcha
        return (
            captcha,
            {
                "category": "captcha_ask",
                "captcha": base64.b64encode(data.read()).decode(),
                "value": captcha,
                "msg": "Are you human?",
                "kwargs": kwargs,
            },
        )
    
    def captcha_ask(self, **kwargs):
        captcha, message = self.captcha_msg(required=True, **kwargs)
        return self.ask(message) == captcha

    def md_msg(self, msg, **kwargs):
        return {"category": "md_show", "msg": msg, "kwargs": kwargs}
    
    def md_show(self, msg, **kwargs):
        """Show markdown

        Args:
            msg (str): markdown string
        """
        self.send_data(self.md_msg(msg, **kwargs), is_slide=True)
        self._queue_in.get()

    def md_show_confirm(self, data, **kwargs):
        """Show a table contains the keys and values of the data dict

        Args:
            data (dict): the data to be shown in the table
        """
        self.send_data({"category": "confirm", "data": data, "kwargs": kwargs}, is_slide=True)
        self._queue_in.get()

    def loading_show(self, msg, wait, **kwargs):
        """Show a progress bar

        Args:
            msg (str): message
            wait (int): the duration (in seconds) of the progress bar

        Keyword Arguments:
            md (bool): render message as markdown
            html (bool): render message as html
        """
        data = {"category": "loading", "msg": msg, "kwargs": kwargs}
        for i in range(wait):
            data["value"] = (i / wait) * 100
            self.send_data(data)
            gevent.sleep(1)

    def new_form(self):
        """Create a new form

        Returns:
            Form: form object
        """
        return Form(self)

    def stop(self, msg=None):
        raise StopChatFlow(msg=msg)


class LegacyChatFLow(GedisChatBot):
    steps = ['chat']

    def __init__(self, method, **kwargs):
        super().__init__(**kwargs)
        self.method = method

    def chat(self):
        self.method(self)
