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

import types


class ACL(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.acl.2")

    @property
    def acl(self):
        raise j.exceptions.Base("cannot modify acl object in acl object")

    @property
    def acl_users_model(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.acl.user.2")
        return self.bcdb.model_get(schema=schemaobj)

    @property
    def acl_circles_model(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.acl.circle.2")
        return self.bcdb.model_get(schema=schemaobj)

    @property
    def users_model(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.user.2")
        return self.bcdb.model_get(schema=schemaobj)

    @property
    def circles_model(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.circle.2")
        return self.bcdb.model_get(schema=schemaobj)

    def _rights_update(self, acl, userids=None, circleids=None, rights=None, action="add"):
        if not userids:
            userids = []
        if not circleids:
            circleids = []
        changed = False
        for userid in userids:
            name = f"user_{acl.name}_{userid}"
            new = False
            for acl_user in acl.users:
                if acl_user.uid == userid:
                    user = acl_user
                    break
            else:
                user = self.acl_users_model.new(name=name)
                user.uid = userid
                new = True
                changed = True

            for right in rights:
                if right not in user.rights and action == "add":
                    user.rights.append(right)
                    changed = True
                elif right in user.rights and action == "delete":
                    user.rights.remove(right)
                    changed = True
            user.save()
            if new:
                acl.users.append(user)

        visited = []
        while circleids:
            circleid = circleids.pop()
            visited.append(circleid)
            name = f"circle_{acl.name}_{circleid}"
            new = False
            for acl_circle in acl.circles:
                if acl_circle.cid == circleid:
                    circle = acl_circle
                    break
            else:
                circle = self.acl_circles_model.new(name=name)
                circle.cid = circleid
                new = True
                changed = True

            for right in rights:
                if right not in circle.rights and action == "add":
                    circle.rights.append(right)
                    changed = True
                elif right in circle.rights and action == "delete":
                    circle.rights.remove(right)
                    changed = True

            circle.save()
            if new:
                acl.circles.append(circle)

            subcircles = self.circles_model.get(circleid).circle_members
            if subcircles:
                for subcircle in subcircles:
                    if subcircle not in visited:
                        circleids.append(subcircle)

        acl.md5 = j.data.hash.md5_string(acl._data)
        acl.save()
        return changed

    def rights_add(self, acl, userids=None, circleids=None, rights=None):
        return self._rights_update(acl, userids=userids, circleids=circleids, rights=rights, action="add")

    def rights_delete(self, acl, userids=None, circleids=None, rights=None):
        return self._rights_update(acl, userids=userids, circleids=circleids, rights=rights, action="delete")

    def _try_get_user(self, id):
        try:
            return self.users_model.get(id)
        except:
            return None

    def _try_get_circle(self, id):
        try:
            return self.circles_model.get(id)
        except:
            return None

    def _compare_rights(self, acl_rights, rights):
        for right in rights:
            if right not in acl_rights:
                return False
        return True

    def _search_users(self, acl, user_id, rights):
        acl_circles = acl.circles
        for acl_circle in acl_circles:
            circle = self.circles_model.get(acl_circle.cid)
            if self._compare_rights(acl_circle.rights, rights):
                for member in circle.user_members:
                    if member == user_id:
                        return True

        return False

    def _search_circles(self, acl, circle_id, rights):
        acl_circles = acl.circles
        for acl_circle in acl_circles:
            if acl_circle.cid == circle_id:
                if self._compare_rights(acl_circle.rights, rights):
                    return True
        return False

    def rights_check(self, acl, id, rights):
        # 1- check if the id is user or circle
        # 2- if user look for it first in acl object then try to find it in any subcircle with the correct rights
        # 3- if circle look for it in all subcircles
        user = self._try_get_user(id)
        circle = self._try_get_circle(id)
        if user:
            for acl_user in acl.users:
                if acl_user.uid == user.id and self._compare_rights(acl_user.rights, rights):
                    return True
            return self._search_users(acl, user.id, rights)
        elif circle:
            return self._search_circles(acl, id, rights)
        else:
            raise RuntimeError(f"Can't find users or circles with id: {id}")

        return False

    def _methods_add(self, obj):
        """
        what does this do?
        :param self:
        :param obj:
        :return:
        """
        obj.rights_add = types.MethodType(self.rights_add, obj)
        obj.rights_delete = types.MethodType(self.rights_delete, obj)
        obj.rights_check = types.MethodType(self.rights_check, obj)

        return obj
