from Jumpscale import j
from enum import Enum  # for enum34, or the stdlib version
from pprint import pprint

TESTTOOLS = j.baseclasses.testtools


class Format(Enum):
    WEBSITE = 1
    BLOG = 2
    WIKI = 3
    DOC = 4
    SOLUTIONPACKAGE = 5
    THREEBOTPACKAGE = 6


class TFGridRegistryClient(j.baseclasses.object, TESTTOOLS):
    """

    A class is used as a client to be able to handle registry actors.

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
        cl = j.clients.gedis.get("registry_client", port=8901, package_name="zerobot.packagemanager")
        cl.reload()
        cl.actors.package_manager.package_add(
            path="/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registry"
        )
        registry_client = j.clients.gedis.get("registry", port=8901, package_name="tfgrid.registry")
        registry_client.reload()

        self.registry_client = registry_client.actors.registry
        self.nacl = self.me.nacl
        self.bcdb = j.data.bcdb.get("threebot_registry")
        self.schema_entry_data = j.data.schema.get_from_text(self.registry_client.get_meta_entry_data().decode())
        self.schema_encrypted_data = j.data.schema.get_from_text(
            self.registry_client.get_meta_encrypted_data().decode()
        )

    def register(
        self,
        authors=None,
        readers=None,
        schema=None,
        model=None,
        is_encrypted_data=False,
        format=Format.WIKI.name,
        schema_url=None,
        location_longitude=None,
        location_latitude=None,
        country_code=None,
        category=None,
        topic=None,
        description=None,
    ):
        """client comes from j.clients.threebot.client_get(threebot="kristof.ibiza").

        client comes from j.clients.threebot.client_get(threebot="kristof.ibiza")

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
            post_id (int): Id of data object saved
        """
        scm = j.data.schema.get_from_text(schema)
        self.registry_client.schema_register(scm.url, schema)

        if is_encrypted_data:
            authors.append(self.me.tid)
            dataobj = self.__add_registry_schema_encrypted_data(
                authors=authors,
                readers=readers,
                threebotclient=self.me,
                new_scm=scm,
                model=model,
                format=format,
                schema_url=schema_url,
                country_code=country_code,
                category=category,
                location_longitude=location_longitude,
                location_latitude=location_latitude,
                topic=topic,
                description=description,
            )
            verifykey, signed_data = self.__sign_data(dataobj=dataobj)
            post_id = self.registry_client.register(
                authors=authors, verifykey=verifykey, input_object=dataobj, signature_hex=signed_data.hex()
            )
            if not post_id:
                raise j.exceptions.Input("Failed to register your content")
            return post_id

        else:
            authors.append(self.me.tid)
            dataobj = self.__add_registry_schema_data(
                authors=authors,
                new_scm=scm,
                model=model,
                format=format,
                schema_url=schema_url,
                location_longitude=location_longitude,
                location_latitude=location_latitude,
                country_code=country_code,
                category=category,
                topic=topic,
                description=description,
            )
            verifykey, signed_data = self.__sign_data(dataobj=dataobj)
            post_id = self.registry_client.register(
                authors=authors, verifykey=verifykey, input_object=dataobj, signature_hex=signed_data.hex()
            )
            if not post_id:
                raise j.exceptions.Input("Failed to register your content")
            return post_id

    def get_data_by_id(self, data_id, tid):
        """Get data by id either encrypted or not.

        Args:
            data_id (int): Id for the requited data.
            tid (int) : Threebot Id.

        Returns:
            info (object): Desired data.
        """
        info = self.registry_client.get(data_id=data_id, tid=tid)
        return info

    def find_encrypted(
        self,
        tid,
        country_code=None,
        format=None,
        category=None,
        location_longitude=None,
        location_latitude=None,
        topic=None,
        description=None,
    ):
        """Find all encrypted data for specific user or you can specify search criteria.

        Args:
            tid (int) : Threebot Id
            country_code (string) : Country code is used for filtering.
            format (string) : Format of the data you want.
            category (string): Category of the data you want.
            topic (string): Topic of the data you want.
            description (string): Description of the data you want.

        Returns:
            res (list): Data in the desired format
        """
        res = self.registry_client.find_encrypted(
            tid=tid,
            country_code=country_code,
            format=format,
            category=category,
            topic=topic,
            description=description,
            location_longitude=location_longitude,
            location_latitude=location_latitude,
        )
        return res

    def find_formatted(
        self,
        schema_url=None,
        country_code=None,
        format=None,
        category=None,
        topic=None,
        description=None,
        location_longitude=None,
        location_latitude=None,
        registered_info_format="jsxschema",
    ):
        """Find the not encrypted data with specific format.

        Args:
            country_code (string) : Country code is used for filtering.
            format (string) = "website,blog,wiki,doc,solutionpackage,threebotpackage" the type of the data
            category (string): Category of the data you want.
            topic (string): Topic of the data you want.
            description (string): Description of the data you want.
            registered_info_format = "jsxschema,yaml,json,msgpack,unstructured" the format of the data


        Returns:
            res (list): Data in the desired format
        """
        res = self.registry_client.find_formatted(
            format=format,
            schema_url=schema_url,
            country_code=country_code,
            category=category,
            topic=topic,
            description=description,
            location_longitude=location_longitude,
            location_latitude=location_latitude,
            registered_info_format=registered_info_format,
        )
        return res.res

    def __add_registry_schema_data(
        self,
        authors=None,
        new_scm=None,
        model=None,
        format=None,
        schema_url=None,
        country_code=None,
        category=None,
        location_longitude=None,
        location_latitude=None,
        topic=None,
        description="",
    ):
        """Add data to the registry.

        Args:
            authors (list): People who contributed in writing the data.
            new_scm (string): Used by BCDB to create the schema for the desired data format by the authors.
            model (object of schema): Actual data stored in BCDB schema.
            format (string) : Format of the data you want.
            description (string) : Description for the registry.

        Returns:

        """
        dataobj = self.bcdb.model_get(url=self.schema_entry_data.url).new()
        dataobj.authors = authors
        dataobj.schema_url = new_scm
        dataobj.registered_info = model._data
        dataobj.format = format
        dataobj.schema_url = schema_url
        dataobj.country_code = country_code
        dataobj.location_longitude = location_longitude
        dataobj.location_latitude = location_latitude
        dataobj.category = category
        dataobj.topic = topic
        dataobj.description = description
        dataobj.save()
        return dataobj

    def __add_registry_schema_encrypted_data(
        self,
        authors=None,
        readers=None,
        new_scm=None,
        model=None,
        format=None,
        schema_url=None,
        country_code=None,
        location_longitude=None,
        location_latitude=None,
        category=None,
        topic=None,
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
        dataobj = self.bcdb.model_get(url=self.schema_entry_data.url).new()
        dataobj.authors = authors
        dataobj.readers = readers
        dataobj.schema_url = new_scm.url
        dataobj.format = format
        dataobj.schema_url = schema_url
        dataobj.country_code = country_code
        dataobj.category = category
        dataobj.topic = topic
        dataobj.location_longitude = location_longitude
        dataobj.location_latitude = location_latitude
        dataobj.description = description
        encrypted_data_model = j.data.schema.get_from_url(url=self.schema_encrypted_data.url).new()
        encrypted_data_model.tid = threebotclient.tid
        # TODO validate if it will be default or not
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

    def __sign_data(self, dataobj):
        pubkey = self.me.nacl.public_key.encode()
        signingkey = self.me.nacl.signing_key.encode()
        verifykey = self.me.nacl.verify_key.encode()
        signed_data = self.me.nacl.sign(dataobj._data)
        return verifykey, signed_data

    def test(self, name=""):
        """
        kosmos 'j.clients.tfgrid_registry.test()'

        """
        self._tests_run(name=name)
