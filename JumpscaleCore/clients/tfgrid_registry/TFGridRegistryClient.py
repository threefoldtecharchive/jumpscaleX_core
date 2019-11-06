from Jumpscale import j
from enum import Enum  # for enum34, or the stdlib version
from pprint import pprint


class Format(Enum):
    WEBSITE = 1
    BLOG = 2
    WIKI = 3
    DOC = 4
    SOLUTIONPACKAGE = 5
    THREEBOTPACKAGE = 6


class TFGridRegistryClient(j.baseclasses.object):
    """A class is used as a client to be able to handle registry actors.

    Attributes
    ----------
    gedis_client (gedis object): Client for Gedis
    registry_client (registry object):used to access registry end points,
    nacl (nacl object):used for signing the data
    bcdb (bcdb object):used to access BDCB database
    """

    __jslocation__ = "j.clients.tfgrid_registry"

    def _init(self, **kwargs):
        # TODO update the threebot with threebot session when it is ready to be used
        self.me = j.tools.threebot.me.get(
            name="test", tid=3, email="test.test@gmail", tname="testUser", pubkey="asdf3dsfasdlfkjasd88893n"
        )
        self.gedis_client = j.servers.threebot.local_start_default(web=True)
        self.gedis_client.reload()
        self.registry_client = self.gedis_client.actors.registry
        self.nacl = self.me.nacl
        self.bcdb = j.data.bcdb.get("threebot_registery")

    def register(
        self, authors=[], readers=[], schema=None, model=None, is_encrypted_data=False, format=Format.WIKI.name
    ):
        """client comes from j.clients.threebot.client_get(threebot="kristof.ibiza").

        register in easy way an object with our without schema

        Args:
            authors (list): People who contributed in writing the data
            readers (list): People who can have access to read the data that has been written by the authors
            schema (string): Used by BCDB to create the schema for the desired data format by the authors.
            model (object of schema): Actual data stored in BCDB schema
            format (string) : Format of the data you want.
            is_encrypted_data (bool): Used to distinguish is that the data will be decrypted or not.

        Raises:
            InputException: Failed to register your content
        Returns:
        """
        scm = j.data.schema.get_from_text(schema)
        self.registry_client.schema_register(scm.url, schema)
        if is_encrypted_data:
            authors.append(self.me.tid)
            dataobj = self.__add_registry_schema_encrypted_data(
                authors=authors,
                readers=[],
                threebotclient=self.me,
                new_scm=scm,
                model=model,
                format=format,
                description="text",
            )
            verifykey, signed_data = self.__sign_data(dataobj=dataobj)
            post_id = self.registry_client.register(
                authors=authors, verifykey=verifykey, input_object=dataobj, signature_hex=signed_data.hex()
            )
            print(post_id)
            if not post_id:
                raise j.exceptions.Input("Failed to register your content")

        else:
            authors.append(self.me.tid)
            dataobj = self.__add_registry_schema_data(
                authors=authors, new_scm=scm, model=model, format=format, description="text"
            )
            verifykey, signed_data = self.__sign_data(dataobj=dataobj)
            post_id = self.registry_client.register(
                authors=authors, verifykey=verifykey, input_object=dataobj, signature_hex=signed_data.hex()
            )
            print(post_id)
            if not post_id:
                raise j.exceptions.Input("Failed to register your content")

    def get_data_by_id(self, data_id, tid):
        """Get data by id either encrypted or not.

        Args:
            data_id (int): Id for the requited data.
            tid (int) : Threebot Id.

        Returns:

        """
        info = self.registry_client.get(data_id=data_id, tid=tid)
        pprint(info)

    def find_encrypted(self, tid, country_code=None, format=None, category=None, topic=None, description=None):
        """Find all encrypted data for specific user or you can specify search criteria.

        Args:
            tid (int) : Threebot Id
            country_code (string) : Country code is used for filtering.
            format (string) : Format of the data you want.
            category (string): Category of the data you want.
            topic (string): Topic of the data you want.
            description (string): Description of the data you want.

        Returns:

        """
        res = self.registry_client.find_encrypted(
            tid=tid, country_code=country_code, format=format, category=category, topic=topic, description=description
        )
        for item in res:
            pprint(f"{item._ddict_hr}")

    def find_formatted(self, format):
        """Find the not encrypted data with specific format.

        Args:
            format(string) : Format of the data you want.
        Returns:

        """
        res = self.registry_client.find_formatted(registered_info_format=format)
        for item in res:
            res = j.data.serializers.jsxdata.loads(item)
            pprint(f"{res._ddict_hr}")

    def __add_registry_schema_data(
        self, url="threebot.registry.entry.data.1", authors=[], new_scm=None, model=None, format=None, description=""
    ):
        """Add data to the registry.

        Args:
            url (string): The url of the schema.
            authors (list): People who contributed in writing the data.
            new_scm (string): Used by BCDB to create the schema for the desired data format by the authors.
            model (object of schema): Actual data stored in BCDB schema.
            format (string) : Format of the data you want.
            description (string) : Description for the registry.

        Returns:

        """
        scm1 = j.data.schema.get_from_url(url=url)
        dataobj = self.bcdb.model_get(url=scm1.url).new()
        dataobj.authors = authors
        dataobj.schema_url = new_scm
        dataobj.registered_info = model._data
        dataobj.format = format
        dataobj.description = description
        dataobj.save()
        return dataobj

    def __add_registry_schema_encrypted_data(
        self,
        url="threebot.registry.entry.data.1",
        authors=[],
        readers=[],
        new_scm=None,
        model=None,
        format=None,
        description="",
        threebotclient=None,
    ):
        """Add encrypted data to registry.

        Args:
            url (string): The url of the schema.
            authors (list): People who contributed in writing the data.
            readers (list): People who can have access to read the data that has been written by the authors
            new_scm (string): Used by BCDB to create the schema for the desired data format by the authors.
            model (object of schema): Actual data stored in BCDB schema.
            format (string) : Format of the data you want.
            description (string) : Description for the registry.
            threebotclient (object threebot): Threebot object of the owner.

        Returns:

        """
        scm1 = j.data.schema.get_from_url(url=url)
        dataobj = self.bcdb.model_get(url=scm1.url).new()
        dataobj.authors = authors
        dataobj.readers = readers
        dataobj.schema_url = new_scm.url
        dataobj.format = format
        dataobj.description = description
        encrypted_data_model = j.data.schema.get_from_url(url="threebot.registry.entry.data_encrypted.1").new()
        encrypted_data_model.tid = threebotclient.tid
        encrypted_data_model.data_ = model._data
        dataobj.registered_info_encrypted = [encrypted_data_model]
        dataobj.save()
        return dataobj

    def __sign_data(self, dataobj):
        """Sign the data.

        Args:
            dataobj (object) : holds all the data for the registry

        Returns:

        """
        pubkey = self.me.nacl.public_key.encode()
        signingkey = self.me.nacl.signing_key.encode()
        verifykey = self.me.nacl.verify_key.encode()
        signed_data = self.me.nacl.sign(dataobj._data)
        return verifykey, signed_data
