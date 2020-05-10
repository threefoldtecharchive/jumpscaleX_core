from functools import wraps
from Jumpscale import j


def actor_method(func):
    def process_doc_str(prefix=None, func=None):
        S = None
        schema_in = None
        schema_out = None

        if func.__doc__:
            for line in func.__doc__.split("\n"):
                line = line.strip()
                if line.startswith("```in") or line.startswith("'''in"):
                    S = "in"
                    schema_text = ""
                elif line.startswith("```out") or line.startswith("'''out"):
                    S = "out"
                    schema_text = ""
                elif line.startswith("```") or line.startswith("'''"):
                    url = "%s.%s" % (prefix, S)
                    url = url.replace("..", ".").strip()
                    if S == "in":
                        schema_in = j.data.schema.get_from_text(schema_text, url=url)
                    else:
                        if schema_text[0].strip() == "!":
                            schema_text = f"out = (O) {schema_text}"
                        schema_out = j.data.schema.get_from_text(schema_text, url=url)
                    S = None
                elif S:
                    schema_text += line + "\n"

        return (schema_in, schema_out)

    @wraps(func)
    def wrapper_action(*args, **kwargs):
        self = args[0]
        if not len(args) == 1:
            raise j.exceptions.Input("actor methods only accept keyword arguments")
        self._log_debug(str(func))
        name = func.__name__
        self._log_debug(name)
        if "user_session" not in kwargs:
            # means not called through the gedis server
            assert "schema_out" not in kwargs

            prefix = "actors.%s.%s.%s" % (self.package.name, self._classname, name)
            # get the schemas
            if name not in self._schemas:
                self._schemas[name] = process_doc_str(prefix=prefix, func=func)
            schema_in, schema_out = self._schemas[name]

            if schema_in:
                if kwargs:
                    data = schema_in.new(datadict=kwargs)
                else:
                    data = schema_in.new()

                for pname in schema_in.propertynames:
                    kwargs[pname] = eval("data.%s" % pname)

            kwargs["user_session"] = j.application.admin_session
            kwargs["schema_out"] = schema_out

        # TODO: j.application.appname is init at this point the error that happens never registed.
        try:
            res = func(self, **kwargs)
        except Exception as e:
            # print("err: ", str(e))
            j.errorhandler.exception_handle(e, die=False)
            raise e
        else:
            return res

    return wrapper_action


def chatflow_step(title=None, disable_previous=False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            self_ = args[0]
            self_.step_info.update(title=title, slide=0, previous=(not disable_previous))
            return func(*args, **kwargs)
        return wrapper
    return decorator


#
# def property_js(func):
#     def wrapper_action(*args, **kwargs):
#         self = args[0]
#         args = args[1:]
#         self._log_debug(str(func))
#         if self._running is None:
#             self.service_manage()
#         name = func.__name__
#         if skip_for_debug or "noqueue" in kwargs:
#             if "noqueue" in kwargs:
#                 kwargs.pop("noqueue")
#             res = func(*args, **kwargs)
#             return res
#         else:
#             event = Event()
#             action = self._action_new(name=name, args=args, kwargs=kwargs)
#             self.action_queue.put((func, args, kwargs, event, action.id))
#             event.wait(1000.0)  # will wait for processing
#             res = j.data.serializers.msgpack.loads(action.result)
#             self._log_debug("METHOD EXECUTED OK")
#             return action
#
#     return wrapper_action
#

# # PythonDecorators/decorator_function_with_arguments.py
# def decorator_function_with_arguments(arg1, arg2, arg3):
#     def wrap(f):
#         print("Inside wrap()")
#         def wrapped_f(*args):
#             print("Inside wrapped_f()")
#             print("Decorator arguments:", arg1, arg2, arg3)
#             f(*args)
#             print("After f(*args)")
#         return wrapped_f
#     return wrap
#
# def do_once2(*args_,**kwargs_):
#     def wrap(func):
#         print("Inside wrap()")
#         def wrapper_action(*args, **kwargs):
#             j.shell()
#             self=args[0]
#             args=args[1:]
#             name= func.__name__
#
#             if name is not "_init":
#                 self._init()
#             if "reset" in kwargs:
#                 reset = kwargs["reset"]
#             else:
#                 reset = False
#             if not self._done_check(name, reset):
#                 res = func(*args,**kwargs)
#                 self._done_set(name)
#                 return res
#         return wrapper_action
#     return wrap
