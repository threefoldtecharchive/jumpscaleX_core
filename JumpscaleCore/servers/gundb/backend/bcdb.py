import re
import json
from .consts import *
from .backend import BackendMixin
import Jumpscale
from Jumpscale import j
from collections import defaultdict

SCHEME_UID_PAT = "(?P<schema>.+?)://(?P<id>.+)"


S = """
@url = proj.todoitem
title** =  "" (S)
done** =  False (B)

@url = proj.todolist
name** = "" (S)
list_todos** =  (LO) !proj.todoitem

@url = proj.simple
attr1** = "" (S)
attr2** = 0 (I)
list_mychars** =  (LS)

@url = proj.email
addr** =  "" (S)

@url = proj.person
name** = "" (S)
email** = "" !proj.email

@url = proj.os
name** = "" (S)

@url = proj.phone
model** =  "" (S)
os** =  "" !proj.os

@url = proj.lang
name** = ""

@url = proj.human
name** = "" (S)
list_favcolors = (LS)
list_langs = (LO) !proj.lang
phone** =  "" !proj.phone

@url = proj.post
name = "" (S)
title** =  "" (S)
body = "" (S)

@url = proj.blog
name** = "" (S)
list_posts = (LO) !proj.post
headline = "" (S)

"""

j.data.schema.get_from_text(S, newest=True)


def parse_schema_and_id(s):
    m = re.match(SCHEME_UID_PAT, s)
    if m:
        return m.groupdict()["schema"], int(m.groupdict()["id"])
    return None, None


class BCDB(BackendMixin):
    def __init__(self, name="test"):
        self.db = defaultdict(lambda: defaultdict(lambda: defaultdict()))
        self.bcdb = None
        try:
            self.bcdb = j.data.bcdb.get(name=name)
        except:
            self.bcdb = j.data.bcdb.get(name=name)

        self.bcdb.reset()

    def get_schema_by_url(self, url):
        schema = j.data.schema.get_from_url(url=url)
        return schema

    def get_model_by_schema_url(self, schema_url):

        return self.bcdb.model_get(url=schema_url)

    def get_object_by_id(self, obj_id, schema=None):
        m = self.get_model_by_schema_url(schema)
        try:
            return m.get(obj_id=obj_id)
        except:
            o = m.new()
            o.save()
            return o

    def set_object_attr(self, obj, attr, val):
        setattr(obj, attr, val)
        return obj

    def save_object(self, obj, obj_id, schema=None):
        obj.save()

    def __setitem__(self, k, v):
        self.db[k] = v

    def __getitem__(self, k):
        return self.db[k]

    def list(self):
        return self.db.items()
