#!/usr/local/opt/python3/bin/python3.5

import datetime
import sys
from getpass import getpass

from Jumpscale.clients.peewee.peewee import *

# from Jumpscale.clients.peewee.peewee import print_
from Jumpscale.clients.peewee.peewee import __version__ as peewee_version
from playhouse.reflection import *
from Jumpscale import j

# TODO: *2 cannot execute, times out on gogs db, should try again

TEMPLATE = """from Jumpscale.clients.peewee.peewee import *%s

database = %s('%s', **%s)

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database
"""

DATABASE_ALIASES = {
    MySQLDatabase: ["mysql", "mysqldb"],
    PostgresqlDatabase: ["postgres", "postgresql"],
    SqliteDatabase: ["sqlite", "sqlite3"],
}

DATABASE_MAP = dict((value, key) for key in DATABASE_ALIASES for value in DATABASE_ALIASES[key])

JSBASE = j.baseclasses.object


class Pwiz(j.baseclasses.object):
    def __init__(
        self, host="127.0.0.1", port=5432, user="postgres", passwd="", dbtype="postgres", dbname="x", schema=None
    ):
        """
        @param type is mysql,postgres,sqlite
        """
        JSBASE.__init__(self)
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.dbtype = dbtype
        self.schema = schema
        self.dbname = dbname
        self._introspector = None

    @property
    def introspector(self):
        if self._introspector is None:
            if self.dbtype not in DATABASE_MAP:
                err("Unrecognized database, must be one of: %s" % ", ".join(DATABASE_MAP.keys()))
                sys.exit(1)
            DatabaseClass = DATABASE_MAP[self.dbtype]
            if self.dbtype == "postgres":
                kwargs = {}
                kwargs["host"] = self.host
                kwargs["port"] = self.port
                kwargs["user"] = self.user
                if self.schema is not None:
                    kwargs["schema"] = self.schema
                kwargs["password"] = self.schema
                db = DatabaseClass(self.dbname, **kwargs)
            else:
                raise j.exceptions.Base("not implemented")
            self._introspector = Introspector.from_database(db, schema=self.schema)
        return self._introspector

    @property
    def codeModel(self):
        database = self.introspector.introspect(table_names=None)
        out = ""

        out += TEMPLATE % (
            self.introspector.get_additional_imports(),
            self.introspector.get_database_class().__name__,
            self.introspector.get_database_name(),
            repr(self.introspector.get_database_kwargs()),
        )

        self._log_debug("INTROSPECTION DONE")

        def _process_table(out, table):
            self._log_debug("Process table:%s" % table)
            # accum = accum or []
            # foreign_keys = database.foreign_keys[table]
            # for foreign_key in foreign_keys:
            #     dest = foreign_key.dest_table
            #
            #     # In the event the destination table has already been pushed
            #     # for printing, then we have a reference cycle.
            #     if dest in accum and table not in accum:
            #         out += '# Possible reference cycle: %s\n' % dest
            #
            #     # If this is not a self-referential foreign key, and we have
            #     # not already processed the destination table, do so now.
            #     if dest not in seen and dest not in accum:
            #         seen.add(dest)
            #         if dest != table:
            #             out += _process_table(out, dest, accum + [table])

            out += "class %s(BaseModel):\n" % database.model_names[table]
            columns = database.columns[table].items()
            columns = sorted(columns)
            primary_keys = database.primary_keys[table]
            for name, column in columns:
                skip = all(
                    [
                        name in primary_keys,
                        name == "id",
                        len(primary_keys) == 1,
                        column.field_class in self.introspector.pk_classes,
                    ]
                )
                if skip:
                    continue
                if column.primary_key and len(primary_keys) > 1:
                    # If we have a CompositeKey, then we do not want to explicitly
                    # mark the columns as being primary keys.
                    column.primary_key = False

                out += "    %s\n" % column.get_field()

            out += "\n"
            out += "    class Meta:\n"
            out += "        db_table = '%s'\n" % table
            multi_column_indexes = database.multi_column_indexes(table)
            if multi_column_indexes:
                out += "        indexes = (\n"
                for fields, unique in sorted(multi_column_indexes):
                    out += "            ((%s), %s),\n" % (", ".join("'%s'" % field for field in fields), unique)
                out += "        )\n"

            if self.introspector.schema:
                out += "        schema = '%s'\n" % self.introspector.schema
            if len(primary_keys) > 1:
                pk_field_names = sorted([field.name for col, field in columns if col in primary_keys])
                pk_list = ", ".join("'%s'" % pk for pk in pk_field_names)
                out += "        primary_key = CompositeKey(%s)\n" % pk_list
            out += "\n"

            self._log_info("OK")
            return out

        seen = set()
        for table in sorted(database.model_names.keys()):
            if table not in seen:
                from pudb import set_trace

                set_trace()
                out += _process_table(out, table)
                seen.add(table)
        return out
