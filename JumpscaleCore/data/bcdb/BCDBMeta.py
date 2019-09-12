# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from Jumpscale import j

JSBASE = j.baseclasses.object

# does not use the schema's any more, now custom dict


class BCDBMeta(j.baseclasses.object):
    """
    #datamodel

    {
        "url":
            {$url:[mid,hasdata,[]]}     #latest md5 is at end of list, nid is the model id
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

    def __init__(self, bcdb=None):

        assert bcdb
        self._bcdb = bcdb

        j.baseclasses.object.__init__(self)

        self._logger_enable()
        self._load()

    def reset(self):
        # make everything in metadata stor empty
        self._reset_runtime_metadata()
        self._bcdb.storclient.delete(0)  # remove the metadata
        self._data = None
        self._load()

    def _reset_runtime_metadata(self):
        # reset the metadata which we can afford to loose
        # all of this can be rebuild from the serialized information of the metastor
        self._data = None

    def _load(self):
        self._reset_runtime_metadata()
        serializeddata = self._bcdb.storclient.get(0)
        if serializeddata is None:
            self._bcdb.storclient.flush()
            self._log_debug("save, empty schema")
            data = {"url": {}, "md5": {}}
            serializeddata = j.data.serializers.msgpack.dumps(data)
            self._bcdb.storclient.set(serializeddata)
            self._data = data
            assert self._bcdb.storclient.get(0) == serializeddata
        else:
            self._log_debug("schemas load from db")
            self._data = j.data.serializers.msgpack.loads(serializeddata)

        for d in self.schema_dicts:
            # this will guarantee right order and make sure the j.data.schema knows about the new schemas
            self._add_to_schema_factory(url=d["url"], md5=d["md5"], text=d["text"])

    def _add_to_schema_factory(self, md5, url, text):
        if text.find("@url") == -1:
            text = "@url = %s\n%s" % (url, text)
        if not j.data.schema.exists(md5=md5):
            j.data.schema._md5_to_schema[md5] = text
        j.data.schema._url_to_md5[url] = md5

    @property
    def schema_dicts(self):
        """
        will walk over the data in the right order (oldest to newest and url's sorted)
        :return:
        """
        urls = [i for i in self._data["url"].keys()]
        urls.sort()
        for url in urls:
            mid, hasdata, md5s = self._data["url"][url]
            for md5 in md5s:
                d = self._data["md5"][md5]
                d2 = d.copy()
                d["md5"] = md5
                d["hasdata"] = hasdata
                yield d

    def _schemas_in_data_print(self):
        for d in self.schema_dicts:
            d2 = d.copy()
            d2["mid"] = self._data["url"][d2["url"]][0]
            d2["hasdata"] = self._data["url"][d2["url"]][1]
            print(" - {url:35} {md5} {mid:3} {hasdata} ".format(**d2))

    def _save(self):
        self._log_debug("save meta:%s" % self._bcdb.name)
        serializeddata = j.data.serializers.msgpack.dumps(self._data)
        self._bcdb.storclient.set(serializeddata, 0)  # we can now always set at 0 because is for sure already there

    def _schema_set(self, schema):
        """
        add the schema to the metadata if it was not done yet
        :param schema:
        :return: the model id
        """

        # optimized for speed, will happen quite a lot, need to know when there is change

        def find_mid():
            mid_highest = 0
            for mid, hasdata, md5s in self._data["url"].values():
                if mid > mid_highest:
                    mid_highest = mid
            return mid_highest + 1

        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise j.exceptions.Base("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        change = False  # we only want to save is there is a change

        # deal with making sure that the md5 of this schema is registered as the newest one
        if schema.url in self._data["url"]:
            mid, hasdata, md5s = self._data["url"][schema.url]
            if schema._md5 in md5s:
                if schema._md5 != md5s[-1]:
                    # means its not the latest one
                    change = True
                    md5s.pop(md5s.index(schema._md5))
                    md5s.append(schema._md5)  # now at end of list again
                    d = [mid, hasdata, md5s]
            elif md5s == []:
                # means was not known yet
                md5s = [schema._md5]
                d = [mid, False, md5s]
            else:
                # is a new one, not in list yet
                change = True
                md5s.append(schema._md5)
                d = [mid, False, md5s]
        else:
            change = True
            d = [find_mid(), False, [schema._md5]]  # initial one has no data
        if change:
            self._data["url"][schema.url] = d

        change2 = False
        if schema._md5 not in self._data["md5"]:
            change2 = True
            d = {}
            d["text"] = schema.text
            d["hasdata"] = schema.hasdata
            d["epoch"] = j.data.time.epoch
            d["url"] = schema.url
            self._data["md5"][schema._md5] = d

        if change or change2:
            self._save()

        # don't load the full schema but put the text of schema there, register to factory
        self._add_to_schema_factory(url=schema.url, md5=schema._md5, text=schema.text)

    def _data_from_url(self, url):
        if url not in self._data["url"]:
            raise j.exceptions.Input("cannot find url in bcbd:%s" % url)
        if len(self._data["url"][url]) == 0:
            raise j.exceptions.Input("cannot find a schema for url in bcbd:%s (no md5s)" % url)
        md5 = self._data["url"][url][-1]
        if md5 not in self._data["md5"]:
            raise j.exceptions.Input("cannot find md5 in bcbd metadata:%s" % md5)
        return self._data["md5"][md5]

    def _mid_from_url(self, url):
        if not url in self._data["url"]:
            raise j.exceptions.Input("cannot find url in metadata for bcdb:%s" % url)
        mid, hasdata, md5s = self._data["url"][url]
        return mid

    def _schema_exists(self, md5):
        return md5 in self._data["md5"]

    def _schema_delete(self, md5):
        if self._schema_exists(md5):
            self._data["md5"].pop(md5)

    def hasdata_set(self, schema):
        assert schema.hasdata  # needs to be True because thats what we need to set
        if not self._schema_exists(schema._md5):
            raise j.exceptions.Value("did not find schema:%s in metadata" % schema._md5)
        url = schema.url
        mid, hasdata, md5s = self._data["url"][url]
        if not hasdata:
            # only save when not set yet
            self._data["url"][url] = [mid, hasdata, md5s]
            self._save()

    def __repr__(self):
        return str(self._schemas_in_data_print())

    __str__ = __repr__
