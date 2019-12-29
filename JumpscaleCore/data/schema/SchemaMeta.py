from Jumpscale import j
import copy

JSBASE = j.baseclasses.object

# does not use the schema's any more, now custom dict


class SchemaMeta(j.baseclasses.object):
    """
    #datamodel

    {
        "url":
            {$url:
                {
                    "sid":sid,
                    "extrafields":{name:propertyline,...},
                    "md5s":[]
                }
                #latest md5 is at end of list, sid is the schema id based on url,

        "md5":
            {
                $md5:
                    {
                        "text":$text,
                        "epoch":$epoch,
                        "url":$url
                    }
            }
    }

    """

    def _init(self):
        self._logger_enable()
        self._data_path = j.core.tools.text_replace("{DIR_CFG}/schema_meta.msgpack")
        self.load()

    def reset(self):
        # make everything in metadata stor empty
        self._data = None
        j.sal.fs.remove(self._data_path)
        self.load()

    def load(self):
        if j.sal.fs.exists(self._data_path):
            self._log_debug("schemas load from db")
            self._data = j.data.serializers.msgpack.load(self._data_path)
        else:
            self._log_debug("save, empty schema")
            data = {"url": {}, "md5": {}}
            serializeddata = j.data.serializers.msgpack.dumps(data)
            j.sal.fs.writeFile(self._data_path, serializeddata)
            self._data = data

    @property
    def schema_dicts(self):
        """
        will walk over the data in the right order (oldest to newest and url's sorted)
        :return:
        """
        urls = [i for i in self._data["url"].keys()]
        urls.sort()
        for url in urls:
            d = self._data["url"][url]
            sid = d["sid"]
            md5s = d["md5s"]
            for md5 in md5s:
                d2 = copy.copy(self._data["md5"][md5])
                d2["md5"] = md5
                d2["sid"] = sid
                yield d2

    def exists(self, md5=None, url=None):
        if md5:
            return md5 in self._data["md5"]
        elif url:
            return url in self._data["url"]
        else:
            return False

    @property
    def schema_urls(self):
        return list(self._data["url"].keys())

    def _schemas_in_data_print(self):
        for d in self.schema_dicts:
            print(f" - {d['url']:35} {d['md5']} {d['sid']:3} ")

    def save(self):
        self._log_debug("save meta schemas")
        serializeddata = j.data.serializers.msgpack.dumps(self._data)
        j.sal.fs.writeFile(self._data_path, serializeddata)

    def schema_exists(self, md5=None, url=None):
        if md5:
            if md5 in self._data["md5"]:
                return True
        elif url:
            if url in self._data["url"]:
                return True
        return False

    def schema_get(self, md5=None, url=None):
        """
        :param md5:
        :param url:
        :return:   dict:
                    {
                        "text":$text,
                        "epoch":$epoch,
                        "url":$url,
                    }
        """
        if md5:
            if md5 in self._data["md5"]:
                return self._data["md5"][md5]
        elif url:
            if url in self._data["url"]:
                return self._data_md5_get(url)
        raise j.exceptions.Input(f"did not find schema in meta with md5:'{md5}' and url '{url}'")

    def extrafields_get(self, url):
        if url in self._data["url"]:
            if "extrafields" not in self._data["url"]:
                self._data["url"]["extrafields"] = {}
                assert self._data["md5s"]
            return self._data["url"]["extrafields"]
        return {}

    def schema_set(self, schema, extrafields={}, save=True):
        """
        add the schema to the metadata if it was not done yet
        :param schema:
        :return: the model id
        """
        # optimized for speed, will happen quite a lot, need to know when there is change
        assert isinstance(extrafields, dict)

        def find_sid():
            sid_highest = 0
            for urldata in self._data["url"].values():
                sid = urldata["sid"]
                if sid > sid_highest:
                    sid_highest = sid
            return sid_highest + 1

        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise j.exceptions.Base("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        change = False  # we only want to save is there is a change

        # deal with making sure that the md5 of this schema is registered as the newest one
        if schema.url in self._data["url"]:
            urldata = self._data["url"][schema.url]
            sid = urldata["sid"]
            md5s = urldata["md5s"]
            if schema._md5 in md5s:
                if schema._md5 != md5s[-1]:
                    # means its not the latest one
                    change = True
                    md5s.pop(md5s.index(schema._md5))
                    md5s.append(schema._md5)  # now at end of list again
                    d = {"sid": sid, "md5s": md5s, "extrafields": extrafields}
            else:
                # is a new one, not in list yet
                change = True
                md5s.append(schema._md5)
                d = {"sid": sid, "md5s": md5s, "extrafields": extrafields}
        else:
            change = True
            d = {"sid": find_sid(), "md5s": [schema._md5], "extrafields": extrafields}
        if change:
            self._data["url"][schema.url] = d

        change2 = False
        if schema._md5 not in self._data["md5"]:
            change2 = True
            d = {}
            d["text"] = schema.text
            d["epoch"] = j.data.time.epoch
            d["url"] = schema.url
            self._data["md5"][schema._md5] = d

            self.schema_backup(schema)
        if (change or change2) and save:
            self.save()

    def schema_link_foreign_md5_get(self, md5):
        if md5 in self._data["md5"]:
            if "link" in self._data["md5"][md5]:
                return self._data["md5"]["link"]

    def schema_link_foreign_md5(self, schema, md5):
        # means we put link fom md5 to other modified schema
        if md5 in self._data["md5"]:
            assert schema.url == self._data["md5"]["url"]
            if "link" in self._data["md5"][md5]:
                return self._data["md5"]["link"]
        d = {}
        d["text"] = ""
        d["epoch"] = j.data.time.epoch
        d["url"] = schema.url
        d["link"] = schema.md5
        self._data["md5"][md5] = d
        self.save()

    def schema_backup(self, schema):
        data = {"url": schema.url, "md5": schema._md5, "text": schema.text, "time": j.data.time.epoch}
        t = j.data.serializers.toml.dumps(data)
        hrtime = j.data.time.epoch
        t2 = "[[time_%s]]\n%s\n\n" % (hrtime, t)
        dest = j.core.tools.text_replace("{DIR_CFG}/bcdb/%s.toml" % schema.url.replace(".", "__"))
        j.sal.fs.writeFile(dest, t2, append=True)

    def _data_md5_get(self, url):
        d = self._data_url_get(url)
        if "md5s" not in d:
            j.shell()
        if len(d["md5s"]) == 0:
            raise j.exceptions.Input("url had no md5:%s" % url)
        md5 = d["md5s"][-1]
        if md5 not in self._data["md5"]:
            raise j.exceptions.Input("cannot find md5 in schema meta: '%s'" % md5)
        return self._data["md5"][md5]

    def _data_url_exists(self, url):
        return url in self._data["url"]

    def _data_url_get(self, url):
        if url not in self._data["url"]:
            raise j.exceptions.Input("cannot find url schema meta" % url)
        d = self._data["url"][url]
        if "extrafields" not in d:
            d["extrafields"] = {}
        return d

    def _sid_from_url(self, url):
        if not url in self._data["url"]:
            raise j.exceptions.Input("cannot find url in metadata for schema meta :'%s'" % url)
        sid, md5s = self._data["url"][url]
        return sid

    def _schema_exists(self, md5):
        return md5 in self._data["md5"]

    def _schema_delete(self, md5):
        if self._schema_exists(md5):
            self._data["md5"].pop(md5)

    def __repr__(self):
        return str(self._schemas_in_data_print())

    __str__ = __repr__
