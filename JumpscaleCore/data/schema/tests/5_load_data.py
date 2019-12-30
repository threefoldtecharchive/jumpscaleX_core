from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.data.schema.test(name="load_data")'

    test loading of data from toml source

    """

    toml = """
        enable = true
        # unique name with dot notation for the package
        name = "digitalme.base"


        [[loaders]]
        giturl = "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base"
        dest = ""

        [[loaders]]
        giturl = "https://github.com/threefoldtech/jumpscaleX_weblibs/tree/master/static"
        dest = "blueprints/base/static"

        """

    schema_package = """
        @url =  jumpscale.digitalme.package
        name = "UNKNOWN" (S)           #official name of the package, there can be no overlap (can be dot notation)
        enable = true (B)
        args = (LO) !jumpscale.digitalme.package.arg
        loaders= (LO) !jumpscale.digitalme.package.loader

        @url =  jumpscale.digitalme.package.arg
        key = "" (S)
        val =  "" (S)

        @url =  jumpscale.digitalme.package.loader
        giturl =  "" (S)
        dest =  "" (S)
        enable = true (B)

        # ENDSCHEMA

        """
    data = j.data.serializers.toml.loads(toml)

    schema_object = j.data.schema.get_from_text(schema_package)
    schema_test = schema_object.new(datadict=data)

    assert schema_test.name == "digitalme.base"
    assert schema_test.enable is True
    assert schema_test.args == []
    assert (
        schema_test.loaders[0].giturl
        == "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base"
    )
    assert schema_test.loaders[0].dest == ""
    assert schema_test.loaders[0].enable is True
    assert schema_test.loaders[1].giturl == "https://github.com/threefoldtech/jumpscaleX_weblibs/tree/master/static"
    assert schema_test.loaders[1].dest == "blueprints/base/static"
    assert schema_test.loaders[1].enable is True

    self._log_info("TEST DONE LOAD DATA")

    return "OK"
