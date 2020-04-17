import json


class BaseClassProperties:
    """
    base class for dealing with properties in redis
    """

    def __init__(self, db, **kwargs):
        self._db = db
        self._key = None

        for key, val in kwargs.items():
            setattr(self, key, val)
        self._protected = False

        self._init(**kwargs)

        self._protected = True
        self._load()

    def _init(self, **kwargs):
        """
        this needs to be overruled
        """
        assert self._key

    def __setattr__(self, name, value):

        if name.startswith("_"):
            self.__dict__[name] = value
            return

        if not self._protected:
            if name not in self.__dict__:
                self.__dict__[name] = None
        else:
            if name not in self.__dict__:
                raise RuntimeError(f"try to write protected argument on {name}")
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 0:
                if value.startswith("'") and value.endswith("'"):
                    value = value.strip("'")
                if value.startswith('"') and value.endswith('"'):
                    value = value.strip('"')
                value = value.strip()

        if self.__dict__[name] != value:
            self.__dict__[name] = value
            # print("-sabe")
            self._save()

    def _load(self):
        if self._db:
            data = self._db.get(self._key)
            if data:
                data2 = json.loads(data.decode())
                self.__dict__.update(data2)

    def _save(self):
        if self._db:
            data = {}
            for key in self.__dict__.keys():
                if not key.startswith("_"):
                    data[key] = getattr(self, key)
            data2 = json.dumps(data)
            self._db.set(self._key, data2)

    def __str__(self):
        out = ""
        for key in self.__dict__.keys():
            if not key.startswith("_"):
                val = getattr(self, key)
                out += f" - {key} : {val}\n"
        return out

    __repr__ = __str__
