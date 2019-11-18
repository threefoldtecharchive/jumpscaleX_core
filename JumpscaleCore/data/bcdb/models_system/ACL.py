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
        """
        updates rights for set of users and/or groups
        :param acl: referance to acl object
        :param userids: list of user ids
        :param circleids: list of circle ids
        :param rights: the rights to be added or deleted
        :param action: "add" or "delete"
        :return: True if any rights were added or deleted
        """
        if not userids:
            userids = []
        if not circleids:
            circleids = []
        changed = False
        for userid in userids:
            name = f"{userid}"
            new = False
            for acl_user in acl.users:
                if acl_user.threebot_id == userid:
                    user = acl_user
                    break
            else:
                user = self.acl_users_model.new(name=name)
                user.threebot_id = userid
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
                if acl_circle.threebot_id == circleid:
                    circle = acl_circle
                    break
            else:
                circle = self.acl_circles_model.new(name=name)
                circle.threebot_id = circleid
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

            subcircles = self.circles_model.find(threebot_id=circleid)
            if subcircles:
                for subcircle in subcircles[0].circle_members:
                    if subcircle not in visited:
                        circleids.append(subcircle)

        acl.md5 = j.data.hash.md5_string(acl._data)
        acl.save()
        return changed

    def rights_add(self, acl, userids=None, circleids=None, rights=None):
        """
        adds rights to set of users or groups
        :param acl: referance tp acl object
        :param userids: list of user threebot ids
        :param circleids: list of circle threebot ids
        :param rights: the rights to be added
        :return: True if any rights were added
        """
        return self._rights_update(acl, userids=userids, circleids=circleids, rights=rights, action="add")

    def rights_delete(self, acl, userids=None, circleids=None, rights=None):
        """
        deletes rights to set of users or groups
        :param acl: referance tp acl object
        :param userids: list of user ids
        :param circleids: list of circle ids
        :param rights: the rights to be deleted
        :return: True if any rights were deleted
        """
        return self._rights_update(acl, userids=userids, circleids=circleids, rights=rights, action="delete")

    def _try_get_user(self, id):
        """
        try to get user from id, if it doesn't exist returns None
        :param id: id to look for
        :return: user object if id exists
        """
        try:
            return self.users_model.find(threebot_id=id)[0]
        except IndexError:
            return None

    def _try_get_circle(self, id):
        """
        try to get circle from id, if it doesn't exist returns None
        :param id: id to look for
        :return: circle object if id exists
        """
        try:
            return self.circles_model.find(threebot_id=id)[0]
        except IndexError:
            return None

    def _compare_rights(self, acl_rights, rights):
        """
        compare two lists of rights and returns True if the first list contains all the items from the second list
        :param acl_rights: the first list which should contains all rights
        :param rights: the second list which should contain the rights we are checking for
        :return: True if all {rights} are in {acl_rights}
        """
        for right in rights:
            if right not in acl_rights:
                return False
        return True

    def _user_has_rights(self, acl, user_id, rights):
        """
        search for certain rights in a user,
        this will iterate over all circles in acl object and check if it contains the current user
        and has the correct rights
        :param acl: referance to acl object
        :param circle_id: current circle id
        :param rights: rights to check
        :return: True if the rights exists
        """
        users =  j.data.bcdb.system.user.find(threebot_id=user_id)
        if not users:
            return False
        user = users[0]
        acl_circles = acl.circles
        for acl_circle in acl_circles:
            circles = self.circles_model.find(threebot_id=acl_circle.threebot_id)
            if not circles:
                continue
            circle = circles[0]
            if self._compare_rights(acl_circle.rights, rights):
                for member in circle.user_members:
                    if member == user.id:
                        return True
        return False

    def _circle_has_rights(self, acl, circle_id, rights):
        """
        search for certain rights in a circle,
        this will iterate over all circles in acl object and check if it contains the current
         circle and has the correct rights
        :param acl: referance to acl object
        :param circle_id: current circle id
        :param rights: rights to check
        :return: True if the rights exists
        """
        acl_circles = acl.circles
        for acl_circle in acl_circles:
            if acl_circle.threebot_id == circle_id:
                if self._compare_rights(acl_circle.rights, rights):
                    return True
        return False

    def rights_check(self, acl, id, rights):
        """
        checks if a certain user or group has certain rights
        :param acl: referance to acl object
        :param id: user threebot_id or circle threebot_id
        :param rights:
        :return:
        """
        # 1- check if the id is user or circle
        # 2- if user look for it first in acl object then try to find it in any subcircle with the correct rights
        # 3- if circle look for it in all subcircles
        user = self._try_get_user(id)
        circle = self._try_get_circle(id)
        if user:
            for acl_user in acl.users:
                if acl_user.name == user.threebot_id and self._compare_rights(acl_user.rights, rights):
                    return True
            return self._user_has_rights(acl, user.name, rights)
        elif circle:
            raise RuntimeError(f"Can't find users or circles with id: {id}")

    def _methods_add(self, obj):
        """
        makes rights_add, rights_delete and rights check available on  object level
        :return:
        """
        obj.rights_add = types.MethodType(self.rights_add, obj)
        obj.rights_delete = types.MethodType(self.rights_delete, obj)
        obj.rights_check = types.MethodType(self.rights_check, obj)

        return obj
