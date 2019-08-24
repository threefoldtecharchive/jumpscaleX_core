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


class actor(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)

    def ping(self):
        return "pong"

    def foo(self):
        return "foo"

    def bar(self):
        return "bar"

    def echo(self, input):
        return input

    def schema_in(self, x):
        """
        ```in
        x = (O) !gedis.test.in
        ```
        """
        return x.foo

    def schema_out(self, schema_out):
        """
        ```out
        !gedis.test.out
        ```
        """
        result = schema_out.new()
        result.bar = "test"
        return result

    def schema_in_out(self, x, schema_out):
        """
        ```in
        x = (O) !gedis.test.in
        ```

        ```out
        !gedis.test.out
        ```
        """
        result = schema_out.new()
        result.bar = x.foo
        return result

    def schema_in_list_out(self, x, schema_out):
        """
        ```in
        x = (O) !gedis.test.in
        ```

        ```out
        schema_out = (LO) !gedis.test.out
        ```
        """
        result = schema_out.new()
        result.bar = x.foo
        return [result, result]

    def args_in(self, foo, bar):
        """
        ```in
        foo = (S)
        bar = (I)
        ```
        """
        return "%s %s" % (foo, bar)

    def raise_error(self):
        raise j.exceptions.Base("woopsy daisy")
