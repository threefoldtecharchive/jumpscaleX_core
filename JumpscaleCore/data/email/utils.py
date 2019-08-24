from json import load
from Jumpscale import j

EMAILS_DIR = j.sal.fs.joinPaths(j.dirs.VARDIR, "email")


def get_msg_path(key):
    ts, _, _ = key.partition("-")
    y, m, d = ts.tm_year, ts.tm_mon, ts.tm_mday
    return j.sal.fs.joinPaths(EMAILS_DIR, y, m, d, key)


def get_json_msg(key):
    return load(get_msg_path(key))
