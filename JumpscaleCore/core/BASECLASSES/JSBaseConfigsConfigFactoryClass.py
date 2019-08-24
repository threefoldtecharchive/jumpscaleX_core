from .JSConfigsFactory import JSConfigsFactory
from .JSFactory import JSFactory
from .JSConfigBCDB import JSConfigBCDB


class JSBaseConfigsConfigFactoryClass(JSConfigBCDB, JSFactory, JSConfigsFactory):
    """
    - 1 data object
    - children which can be object_config_bcdb or objects_config_bcdb or any other


    """

    pass
    # def __init__(self, **kwargs):
    #     JSConfigsFactory.__init__(**kwargs)
    #     JSConfig.__init__(**kwargs)
