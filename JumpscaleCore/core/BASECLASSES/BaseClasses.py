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
from .TestTools import TestTools
from .JSFactory import *
from .JSDict import JSDict


class BaseClasses:
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
    def object_config_base(self):
        """
        the base class as used by object_config_bcdb and object_config_collection

        deals with base functionality as required for the object(s)_config classes

        - triggers
        - change schema's inside object
        - initialization

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
    def factory(self):
        """
        factory class is combination of jsxobject+testtools+factory class

        functions

        - use _ChildClass(es) functionality to create children
        - recursive delete & reset
        - can have an own jsxobject attached to it

        to have jsxobject attached:

            attach the object or the factory class for the object (jsx object model)

            def _init():
                self._object_config=... if you manually fetch object

            or specify the factory

            def _init():
                self._object_config_factory= ...

            this one will be used to create an object with _object_config_factory.new(name=...)

        :return:
        """
        return JSFactory

    @property
    def factory_protected(self):
        """
        same as factory but attributes protected
        """
        return JSFactoryProtected

    @property
    def factory_testtools(self):
        """
        same as factory but testtools added e.g. self.test()
        """
        return JSFactoryTesttools

    @property
    def factory_protected_testtools(self):
        """
        same as factory but attributes protected
        & testtools added e.g. self.test()
        """
        return JSFactoryProtectedTesttools

        # self.JSFactoryConfigsBaseClass = JSFactoryConfigsBaseClass  # for e.g. clients, factory for 1 type of children

        # self.JSBaseConfigsClass = JSBaseConfigsClass  # multiple config children
        # self.JSConfigsFactory = JSConfigsFactory

        # self.JSBaseConfigsFactoryClass = JSBaseConfigsFactoryClass
        # self.JSBaseFactoryClass = JSBaseFactoryClass
        # self.JSConfigClass = JSConfig
        # self._JSDictClass = JSDict
        # self.ThreeBotPackageBase = ThreeBotPackageBase
        # self.ThreeBotActorBase = ThreeBotActorBase
        # self.JSBaseConfigsConfigFactoryClass = JSBaseConfigsConfigFactoryClass


# ### the base ones
# from .BASECLASSES.JSBase import JSBase
# from .BASECLASSES.JSFactoryTools import JSFactoryTools
#
# ####
#
# from .BASECLASSES.JSConfig import JSConfig
# from .BASECLASSES.JSConfigs import JSConfigs
# from .BASECLASSES.JSConfigsFactory import JSConfigsFactory
# from .BASECLASSES.ThreeBotActorBase import ThreeBotActorBase
# from .BASECLASSES.JSDict import JSDict
#
# class JSGroup:
#     pass
#
#
# class JSFactoryConfigsBaseClass(JSFactoryTools, JSConfigs):
#     """
#     as used for j.... factory classes will has constructor for 1 type of Config children
#
#     class myclass(j.application.JSFactoryConfigsBaseClass):
#         def _init(self,**kwargs):
#             ...
#
#     """
#
#     pass
#
#
# class JSBaseConfigsClass(JSConfigs):
#     """
#     is not for a factory (doesn't have the test or __location__ inside
#     has support for 1 type of children
#     """
#
#     pass
#
#
# class JSBaseConfigClass(JSConfig):
#     """
#     no children, only 1 data object
#     """
#
#     pass
#
#
# class JSBaseConfigsFactoryClass(JSFactoryTools, JSConfigsFactory):
#     """
#     no children, only 1 data object
#     """
#
#     pass
#
#


# self._JSGroup = JSGroup
