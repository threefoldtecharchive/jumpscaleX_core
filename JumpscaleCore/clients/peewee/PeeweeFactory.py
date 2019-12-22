from Jumpscale import j
from .peeweeClient import PeeweeClient

import importlib

# dont use the system one
# from .peewee import *

import uuid


class PeeweeFactory(j.baseclasses.object_config_collection_testtools):
    """
    """

    __jslocation__ = "j.clients.peewee"
    _CHILDCLASS = PeeweeClient

    def _init(self, **kwargs):
        self.__imports__ = "peewee"
        self.clients = {}

        from .peewee import (
            PrimaryKeyField,
            BlobField,
            Model,
            BooleanField,
            TextField,
            CharField,
            IntegerField,
            SqliteDatabase,
            FloatField,
            DateTimeField,
            ForeignKeyField,
            IntegrityError,
        )

        self.PrimaryKeyField = PrimaryKeyField
        self.DateTimeField = DateTimeField
        self.BlobField = BlobField
        self.Model = Model
        self.BooleanField = BooleanField
        self.TextField = TextField
        self.CharField = CharField
        self.IntegerField = IntegerField
        self.SqliteDatabase = SqliteDatabase
        self.FloatField = FloatField
        self.ForeignKeyField = ForeignKeyField
        self.IntegrityError = IntegrityError

    def test_model_create(self, psqlclient):
        pass

    def test(self):
        """
        kosmos 'j.clients.peewee.test()'
        :return:
        """

        # j.builders.db.psql.start()
        # cl = j.clients.postgres.db_client_get()
        # cl.db_create("pewee_test")

        pw = self.get(name="test", dbname="mydb", login="despiegk", passwd_="123456", port=54320)
        db = pw.db
        pw.save()

        class BaseModel(self.Model):
            class Meta:
                database = db

        class User(BaseModel):
            username = self.TextField(unique=True)

            class Meta:
                table_name = "user"

        class Tweet(BaseModel):
            content = self.TextField()
            content2 = self.TextField()
            content3 = self.TextField()
            timestamp = self.DateTimeField()
            user = self.ForeignKeyField(column_name="user_id", field="id", model=User)

            class Meta:
                table_name = "tweet"

        class Tweet3(BaseModel):
            name = self.CharField(unique=True)
            content2 = self.TextField(index=True)
            content3 = self.CharField(index=True)

        with db:
            db.create_tables([User, Tweet])

        u = User()
        u.username = uuid.uuid4().hex[:6].upper()

        u.save()
        # m = pw.model_get()

        def create():
            # Tweet3.drop_table()
            db.create_tables([Tweet3])
            start = Tweet3.select().count() + 1
            for i in range(start, 1000000):
                if i / 1000 == int(i / 1000):
                    print(i)
                # w = Tweet3.get(Tweet3.name == "name%s" % i)
                # if not w:
                u = Tweet3()
                u.name = "name%s" % i
                u.content2 = "this is some content %s + 1" % i
                u.content3 = "this is some content %s + 2" % i
                u.save()

        def query():
            for i in range(10000):
                i = j.data.idgenerator.generateRandomInt(fromInt=2, toInt=10000)
                w = Tweet3.get(Tweet3.name == "name%s" % i)

        create()
        query()

        return "TESTS OK"
