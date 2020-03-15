from Jumpscale import j

from .JSXObjectBase import JSXObjectBase


class JSXObjectSub(JSXObjectBase):
    def _init_pre(self, capnpdata=None, datadict=None, schema=None):

        # assert parent
        assert self._parent
        self._model = None

        current = self
        while current._parent:
            current = current._parent
        self._root = current

        return JSXObjectBase._init_pre(self, capnpdata=capnpdata, datadict=datadict, schema=schema)

    def save(self, serialize=True):
        return self._root._save_root(serialize=serialize)
