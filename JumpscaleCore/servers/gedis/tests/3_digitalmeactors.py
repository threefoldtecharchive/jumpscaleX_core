from Jumpscale import j


def main(self):

    """
    this method is only used when not used in digitalme
    kosmos 'j.servers.gedis.test_server_start()'

    """
    gedis = self.get(name="test")

    zdb = j.servers.zdb.test_instance_start(reset=False)
    zdb_cl = zdb.client_admin_get()
    bcdb = j.data.bcdb.get(zdbclient=zdb_cl, name="test")
    path = j.clients.git.getContentPathFromURLorPath(
        "https://github.com/threefoldtech/digital_me/tree/master/packages/examples/models"
    )
    bcdb.models_add(path=path)

    path = j.clients.git.getContentPathFromURLorPath(
        "https://github.com/threefoldtech/digital_me/tree/master/packages/examples/actors"
    )
    gedis.actors_add(namespace="gedis_examples", path=path)
    gedis.models_add(namespace="gedis_examples", models=bcdb)

    gedis.start()
