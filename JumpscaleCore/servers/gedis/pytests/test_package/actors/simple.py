from Jumpscale import j

JSBASE = j.baseclasses.object

# SCHEMA_IN = """
# @url = gedis.test.in
# foo = (S)
# """

# SCHEMA_OUT = """
# @url = gedis.test.out
# bar = (S)
# """


class simple(JSBASE):
    def __init__(self, **kwargs):
        JSBASE.__init__(self)

    @j.baseclasses.actor_method
    def ping(self):
        return "pong"

    @j.baseclasses.actor_method
    def foo(self):
        return "foo"

    @j.baseclasses.actor_method
    def bar(self):
        return "bar"

    @j.baseclasses.actor_method
    def echo(self, input):
        return input
