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


class actor(j.baseclasses.threebot_actor):
    def _init(self, **kwargs):
        for schema in [SCHEMA_IN, SCHEMA_OUT]:
            j.data.schema.get_from_text(schema)

    def foo(self, user_session=None):
        return "foo"

    def bar(self, user_session=None):
        return "bar"

    def echo(self, _input, user_session=None):
        return _input

    def schema_in(self, x, user_session=None):
        """
        ```in
        x = (O) !gedis.test.in
        ```
        """
        return x.foo

    def schema_out(self, schema_out=None, user_session=None):
        """
        ```out
        !gedis.test.out
        ```
        """
        result = schema_out.new()
        result.bar = "test"
        return result

    def schema_in_out(self, x, schema_out=None, user_session=None):
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

    def schema_in_list_out(self, x, schema_out=None, user_session=None):
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

    def args_in(self, foo, bar, user_session=None):
        """
        ```in
        foo = (S)
        bar = (I)
        ```
        """
        return "%s %s" % (foo, bar)

    def raise_error(self, user_session=None):
        raise j.exceptions.Base("woopsy daisy")
