from Jumpscale import j
from .JSConfigBCDB import JSConfigBCDB

"""
classes who use JSXObject for data storage but provide nice interface to enduser
"""


class JSConfigBCDBRedis(JSConfigBCDB):
    def _init_jsconfig(self, jsxobject=None, datadict=None, name=None, **kwargs):

        self._model_ = False
        self._bcdb_ = None

        if name in kwargs:
            name = kwargs.pop("name")

        if not name:
            if jsxobject is not None:
                name = jsxobject.name

        if not name:
            name = "default"

        if jsxobject:
            self._data = jsxobject
        else:
            self._data = self._schema.new()

        key = self._schema.url.replace(".", "__")
        self._redis_key = "bcdb:redis:%s" % key

        self._data.name = name

        self.load()

        if kwargs:
            if not datadict:
                datadict = {}
            datadict.update(kwargs)

        if datadict:
            assert isinstance(datadict, dict) or isinstance(datadict, j.baseclasses.dict)
            self._data_update(datadict)

        assert self._data.name

        if "autosave" in kwargs:
            self._data._autosave = j.data.types.bool.clean(kwargs["autosave"])

    def delete(self, reset=True):
        """
        :return:
        """
        j.core.db.hdel(self._redis_key, self.name)
        if reset:
            self.reset()

    def reset(self):
        self._data.delete()

    def load(self):
        """
        load from bcdb
        :return:
        """
        if j.core.db.hexists(self._redis_key, self.name):
            jsondata = j.core.db.hget(self._redis_key, self.name).decode()
            self._data_update(j.data.serializers.json.loads(jsondata))

        return self

    def save(self):
        j.core.db.hset(self._redis_key, self.name, self._data._json)
