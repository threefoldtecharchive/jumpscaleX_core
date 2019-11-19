from functools import wraps
from Jumpscale import j


def actor_method(func):
    def process_doc_str(func):
        S = None
        schema_in = None
        schema_out = None
        for line in func.__doc__.split("\n"):
            line = line.strip()
            if line.startswith("```in") or line.startswith("'''in"):
                S = "in"
                schema_text = ""
            elif line.startswith("```out") or line.startswith("'''out"):
                S = "out"
                schema_text = ""
            elif line.startswith("```") or line.startswith("'''"):
                if S == "in":
                    schema_in = j.data.schema.get_from_text(schema_text)
                else:
                    schema_out = j.data.schema.get_from_text(schema_text)
                S = None
            elif S:
                schema_text += line + "\n"

        return (schema_in, schema_out)

    @wraps(func)
    def wrapper_action(*args, **kwargs):
        self = args[0]
        if not len(args) == 1:
            raise j.exceptions.Input("we should not call an actor method with args")
        self._log_debug(str(func))
        name = func.__name__
        self._log_debug(name)
        if "user_session" not in kwargs:
            # means not called through the gedis server
            assert "schema_out" not in kwargs

            # get the schemas
            if name not in self._schemas:
                self._schemas[name] = process_doc_str(func)
            schema_in, schema_out = self._schemas[name]

            if schema_in:
                data = schema_in.new(datadict=kwargs)
                for pname in schema_in.propertynames:
                    kwargs[pname] = eval("data.%s" % pname)

            kwargs["user_session"] = None
            kwargs["schema_out"] = schema_out

        res = func(self, **kwargs)
        return res

    return wrapper_action


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
