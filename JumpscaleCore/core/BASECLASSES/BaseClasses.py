# Copyright (C) July 2018:  TF TECH NV in Belgium see https://www.threefold.tech/
# In case TF TECH NV ceases to exist (e.g. because of bankruptcy)
#   then Incubaid NV also in Belgium will get the Copyright & Authorship for all changes made since July 2018
#   and the license will automatically become Apache v2 for all code related to Jumpscale & DigitalMe
# This file is part of jumpscale at <https://github.com/threefoldtech>.
# jumpscale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jumpscale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License v3 for more details.
#
# You should have received a copy of the GNU General Public License
# along with jumpscale or jumpscale derived works.  If not, see <http://www.gnu.org/licenses/>.
# LICENSE END


from .JSBase import JSBase
from .JSConfigBCDB import JSConfigBCDB
from .JSConfigsBCDB import JSConfigsBCDB
from .JSConfigBCDBBase import JSConfigBCDBBase
from .ThreeBotActorBase import ThreeBotActorBase
from .ThreeBotPackageBase import ThreeBotPackageBase
from .ThreeBotFactoryBase import ThreeBotFactoryBase
from .TestTools import TestTools
from .JSFactory import JSFactory
from .JSDict import JSDict


class BaseClasses(JSBase, TestTools):
    def __init__(self):
        pass

    @property
    def dict(self):
        """
        our own dict implementation

        """
        return JSDict

    @property
    def object(self):
        """
        the lowest level class for a generic usable object
        every object in Jumpscale inherits from this one

        functions

        - logging
        - initialization of the class level stuff
        - caching logic
        - logic for auto completion in shell
        - state on execution of methods (the _done methods)

        """
        return JSBase

    @property
    def object_config(self):
        """
        configuration object as used in kosmos
        with data stored in bcdb
        bcdb can be memory only, which means is not persisted
        :return:
        """
        return JSConfigBCDB

    @property
    def object_config_collection(self):
        """
        configuration objects factory as used in kosmos
        with data stored in bcdb
        bcdb can be memory only, which means is not persisted

        has new,list,get,save... methods

        is e.g. cars containing a collection off car

        :return:
        """
        return JSConfigsBCDB

    @property
    def object_config_collection_testtools(self):
        """

        :return:
        configuration objects factory as used in kosmos
        with data stored in bcdb
        bcdb can be memory only, which means is not persisted

        has new,list,get,save... methods

        is e.g. cars containing a collection off car

        this one also protects the attributes and has the TestTools added to it

        :return:
        """

        class JSConfigsBCDBFactory(JSConfigsBCDB, TestTools):
            pass

        return JSConfigsBCDBFactory

    @property
    def object_config_base(self):
        """
        the base class as used by object_config and object_config_collection

        deals with base functionality as required for the object(s)_config classes

        - triggers
        - change schema's inside object
        - initialization

        is useful to test classes against isinstance(...)

        :return:
        """
        return JSConfigBCDBBase

    @property
    def threebot_actor(self):
        """
        the base class for developing actors in threebot

        :return:
        """
        return ThreeBotActorBase

    @property
    def threebot_package(self):
        """
        the base class for a package class for a therebot

        :return:
        """
        return ThreeBotPackageBase

    @property
    def threebot_factory(self):
        """
        the base class for a package factory

        :return:
        """
        return ThreeBotFactoryBase

    @property
    def testtools(self):
        """
        implement some methods to deal with testing, is used on factories of jumpscale
        provides e.g. $object.test()

        can not be used individual, neeeds to be combined with jsobject  class

        :return:
        """
        return TestTools

    @property
    def builder(self):
        """
        baseclass to create a builder

        :return:
        """
        from .BuilderBaseClass import BuilderBaseClass

        return BuilderBaseClass

    @property
    def builder_method(self):
        """
        decorator method for builder base class
        """
        from .BuilderBaseClass import builder_method

        return builder_method

    @property
    def factory(self):
        """
        factory class is combination of jsxobject+factory class

        functions

        - use _ChildClass(es) functionality to create children
        - recursive delete & reset
        - can have an own jsxobject attached to it

        example see /sandbox/code/github/threefoldtech/jumpscaleX_libs/tutorials/base/object_structure/BaseClasses_ConfigObjects.py

        this type of class will show all the objects of the type


        :return:
        """

        return JSFactory

    @property
    def factory_testtools(self):
        """
        factory class is combination of jsxobject+factory class

        functions

        - use _ChildClass(es) functionality to create children
        - recursive delete & reset
        - can have an own jsxobject attached to it

        example see /sandbox/code/github/threefoldtech/jumpscaleX_libs/tutorials/base/object_structure/BaseClasses_ConfigObjects.py

        this type of class will show all the objects of the type


        :return:
        """

        class JSFactoryDataTesttools(JSFactory, TestTools):
            pass

        return JSFactoryDataTesttools

    @property
    def factory_data(self):
        """
        factory class is combination of jsxobject+factory class

        functions

        - use _ChildClass(es) functionality to create children
        - recursive delete & reset
        - can have an own jsxobject attached to it

        example see /sandbox/code/github/threefoldtech/jumpscaleX_libs/tutorials/base/object_structure/BaseClasses_ConfigObjects.py

        this one acts as a parent, only the children will be shown


        :return:
        """

        class JSFactoryData(JSConfigBCDB, JSFactory):
            pass

        return JSFactoryData

    @property
    def factory_data_testtools(self):
        """

        :return:
        """

        class JSFactoryDataTesttools(JSConfigBCDB, JSFactory, TestTools):
            pass

        return JSFactoryDataTesttools
