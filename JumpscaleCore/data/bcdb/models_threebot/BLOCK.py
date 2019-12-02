from Jumpscale import j


class BLOCK(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.fs.block.2")
