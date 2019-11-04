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


from Jumpscale import j
from .JSBase import JSBase

from .JSBase import JSBase
from .ThreeBotActorBase import ThreeBotActorBase


class ThreeBotCRUDActorBase(ThreeBotActorBase):
    def new(self, **kwargs):
        user_session = kwargs.pop("user_session")
        # TODO: use user_session for authentication

        return self.model.set_dynamic(kwargs)

    def set(self, **kwargs):
        user_session = kwargs.pop("user_session")
        # TODO: use user_session for authentication

        id = kwargs.pop("object_id")
        obj = self.model.get(id)

        for key, val in kwargs.items():
            if val:
                setattr(object, key, val)
        obj.save()
        return obj

    def get_by_name(self, **kwargs):
        return self.model.get_by_name(kwargs["name"])

    def get(self, **kwargs):
        return self.model.get(kwargs["object_id"])

    def find(self, **kwargs):
        return self.model.find(**kwargs["query"])

    def delete(self, **kwargs):
        obj = self.model.get(kwargs["object_id"])
        obj.delete()
