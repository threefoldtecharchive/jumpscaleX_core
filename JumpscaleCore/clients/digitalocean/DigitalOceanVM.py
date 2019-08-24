from Jumpscale import j

import digitalocean
import time

JSConfigBase = j.baseclasses.object_config


class DigitalOceanVM(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.digitalocean.vm
    name* = "" (S)
    client_name = "" (S)
    project_name = "" (S)
    do_id = "" (S)
    meta = {} (DICT)
    """

    def _init(self, **kwargs):
        j.shell()
