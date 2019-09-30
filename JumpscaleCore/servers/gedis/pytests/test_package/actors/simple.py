from Jumpscale import j

JSBASE = j.baseclasses.object

SCHEMA_IN = """
@url = gedis.test.in
foo = (S)
"""

SCHEMA_OUT = """
@url = gedis.test.out
bar = (S)
"""


class simple(JSBASE):
    def __init__(self, **kwargs):
        JSBASE.__init__(self)

    def ping(self):
        return "pong"

    def foo(self):
        return "foo"

    def bar(self):
        return "bar"

    def echo(self, input):
        return input
