from Jumpscale import j
import binascii
from .ThreebotMe import ThreebotMe


class ThreebotMeCollection(j.baseclasses.object_config_collection):
    _CHILDCLASS = ThreebotMe
    _classname = "me"

    @property
    def default(self):
        """
        your default threebot data
        :return:
        """
        return self.get(name="default")
