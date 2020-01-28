from Jumpscale import j


def test014_base_classes():
    """
    to run:

    kosmos 'j.data.types.test(name="baseclasses")'
    """

    # some basic tests for code completion, doesn't really belong here but needs to be done
    class A(j.baseclasses.object):
        def _init(self, a, b):
            self.a = a
            self.b = b

        def shout(self):
            pass

        def some(self):
            pass

    a = A(a="1", b=2)

    assert "a" in a._properties  # if fail means properties not well calculated
    assert "b" in a._properties

    assert len(a._methods_names_get(filter="s*")) == 2
    assert len(a._methods_names_get(filter="some")) == 1
    assert len(a._properties_names_get(filter="*")) == 2
    assert len(a._methods_names_get()) == 2

    j.data.types._log_info("TEST DONE FOR BASECLASSES")

    return "OK"
