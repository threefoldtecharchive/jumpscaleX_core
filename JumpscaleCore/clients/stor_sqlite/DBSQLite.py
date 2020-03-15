from Jumpscale import j


class DBSQLite(j.baseclasses.object):
    def _init(self, bcdbname=None, readonly=False, **kwargs):

        assert bcdbname
        assert "name" not in kwargs
        self.bcdbname = bcdbname

        self.type = "SDB"

        self.readonly = readonly

        self._dbpath = j.core.tools.text_replace("{DIR_VAR}/bcdb/%s/sqlite_stor.db" % self.bcdbname)

        self.sqlitedb = None

        self._connect()

    def _connect(self):

        if self.readonly:
            self._log_info("sqlite file is in readonly mode for: '%s'" % self.bcdbname)
            db_path = j.core.tools.text_replace("file:%s?mode=ro" % self._dbpath)
        else:
            db_path = j.core.tools.text_replace("file:%s" % self._dbpath)

        if j.sal.fs.exists(self._dbpath):
            self._log_debug("EXISTING SQLITEDB in %s" % self._dbpath)
        else:
            j.sal.fs.touch(self._dbpath)
            self._log_debug("NEW SQLITEDB in %s" % self._dbpath)

        self.sqlitedb = j.data.peewee.SqliteDatabase(db_path, uri=True, pragmas={"journal_mode": "wal"})
        if self.sqlitedb.is_closed():
            self.sqlitedb.connect()

        p = j.data.peewee

        class BaseModel(p.Model):
            class Meta:
                database = self.sqlitedb

        class KVS(BaseModel):
            id = p.PrimaryKeyField()
            value = p.BlobField()

        self._table_model = KVS
        self._table_model.create_table()

    def stop(self):
        if not self.sqlitedb.is_closed():
            self.sqlitedb.close()

    @property
    def nsinfo(self):
        return {"entries": self.count}

    def set(self, data, key=None):
        if key is None:
            res = self._table_model(value=data)
            res.save()
            return res.id - 1
        else:
            key = int(key)
            if self.exists(key):
                if self.get(key) == data:
                    return None
                self._table_model.update(value=data).where(self._table_model.id == (key + 1)).execute()
            else:
                self._table_model.create(id=(key + 1), value=data)
        return key

    def exists(self, key):
        return self.get(key) != None

    def flush(self):
        """
        will remove all data from the database DANGEROUS !!!!
        :return:
        """
        self._log_info("RESET FOR KVS")
        self._table_model.delete().execute()
        self._table_model.create_table()
        assert self._table_model.select().count() == 0

    @property
    def count(self):
        return self._table_model.select().count()

    def get(self, key):
        res = self._table_model.select().where(self._table_model.id == (int(key) + 1))
        if len(res) == 0:
            return None
        elif len(res) > 1:
            raise j.exceptions.Base("error, can only be 1 item")
        return res[0].value

    def list(self, key_start=None, reverse=False):
        result = []
        if key_start:
            key_start = key_start + 1
        for key, data in self.iterate(key_start=key_start, reverse=reverse, keyonly=False):
            result.append(key)
        return result

    def delete(self, key):
        return self._table_model.delete_by_id(int(key) + 1)

    def iterate(self, key_start=None, **kwargs):
        if key_start:
            items = self._table_model.select().where(getattr(self._table_model, "id") >= key_start)
        else:
            items = self._table_model.select()
        for item in items:
            yield ((item.id) - 1, self.get(item.id - 1))

    def close(self):
        if self.sqlitedb:
            self.sqlitedb.close()
