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
    def user(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.acl.user.2")
        return self.bcdb.model_get(schema=schemaobj)

    @property
    def circle(self):
        schemaobj = j.data.schema.get_from_url("jumpscale.bcdb.acl.circle.2")
        return self.bcdb.model_get(schema=schemaobj)

    def add_acl_users(self, users):
        acl_users = []
        for k, v in users.items():
            user = self.bcdb.user.get(k)
            acl_users.append(user)
            model_acl_user = self.user.new()
            model_acl_user.name = "user_%s" % k
            model_acl_user.uid = k
            model_acl_user.rights = v
            model_acl_user.save()
        return acl_users

    def add_acl_circles(self, circles, visited=[]):
        """
        to add the circles in acl.circle and check all ( users , circles) to get it
        
        circles: circles id and rights 
        visited: help variable of recursion to check circle of circle
        
        """
        acl_circles = []
        acl_circles_user = {}
        acl_circles_member = {}
        for k, v in circles.items():
            circle = self.bcdb.circle.get(k)
            for i in circle.circle_members:
                if k not in visited:
                    acl_circles_member[i] = v
                    visited.append(k)

            if acl_circles_member != {}:
                self.add_acl_circles(acl_circles_member, visited)

            for i in circle.user_members:
                acl_circles_user[i] = v
            self.add_acl_users(acl_circles_user)
            acl_circles.append(circle)
            model_acl_circle = self.circle.new()
            model_acl_circle.name = "circle_%s" % k
            model_acl_circle.cid = k
            model_acl_circle.rights = v
            model_acl_circle.save()
        return acl_circles

    def rights_set(self, acl, userids=[], circleids=[], rights="r"):
        """
        userid can be list of userid or userid
        :param acl:
        :param users:
        :param rights:
        :return:
        """

        rights = j.data.types.string.unique_sort(rights).lower()  # lets make sure its sorted & unique

        if not j.data.types.list.check(userids):
            raise j.exceptions.Base("userids needs to be list")
        if not j.data.types.list.check(circleids):
            raise j.exceptions.Base("circleids needs to be list")

        rdict = acl._ddict

        change = False

        def do(itemsToFind, rdict, key, rights, change):
            circle = rdict[key]

            for i in itemsToFind:
                i = int(i)
                if i in circle:
                    original = j.data.types.string.unique_sort(circle[i]).lower()
                    if original != rights:
                        change = True
                        circle[i] = rights
                else:
                    # does not exist yet
                    change = True
                    circle[i] = rights
            return change, rdict

        change, rdict = do(userids, rdict, "users", rights, change)
        change, rdict = do(circleids, rdict, "circles", rights, change)

        if change:
            for key, value in rdict.items():
                if key == "users":
                    acl.users = self.add_acl_users(value)
                elif key == "circles":
                    acl.circles = self.add_acl_circles(value)
                else:
                    setattr(acl, key, value)
            acl.md5 = j.data.hash.md5_string(acl._data)
            acl.save()

        return change

    def rights_check(self, acl, id, rights):
        def rights_check_user_group(rights2check, rightsInObj):
            for item in rights2check:
                if item not in rightsInObj:
                    return False
            return True

        user_or_cirlce_id = int(id)
        for user in acl.users:
            if user.id == user_or_cirlce_id:
                user_rights = self.user.get_by_name("user_%s" % user_or_cirlce_id)[0]
                return rights_check_user_group(rights, user_rights.rights)

        for circle in acl.circles:
            if circle.id == id:
                circle = self.circle.get_by_name("circle_%s" % circle.id)[0]
                if circle:
                    if rights_check_user_group(rights, circle.rights):
                        return True
        return False

    def _methods_add(self, obj):
        """
        what does this do?
        :param self:
        :param obj:
        :return:
        """
        obj.rights_set = types.MethodType(self.rights_set, obj)
        obj.rights_check = types.MethodType(self.rights_check, obj)

        return obj

    def _dict_process_out(self, d):
        res = {}
        self._log_debug("dict_process_out:\n%s" % d)
        for circle in d["circles"]:
            if circle.get("id"):
                r = self.circle.get_by_name("circle_%s" % circle["id"])[0]
                r = "".join(r.rights)
                acl_circle = self.circle.get_by_name("circle_%s" % circle["id"])[0]
                res[acl_circle.cid] = r  # as string
        d["circles"] = res
        res = {}
        for user in d["users"]:
            if user.get("id"):
                r = self.user.get_by_name("user_%s" % user["id"])[0]
                r = "".join(r.rights)
                acl_user = self.user.get_by_name("user_%s" % user["id"])[0]
                res[acl_user.uid] = r  # as string
        d["users"] = res
        return d

    def _dict_process_in(self, d):
        res = {}
        res["hash"] = d["hash"]
        res["circles"] = []
        res["users"] = []
        for uid, rights in d["circles"].items():
            res["circles"].append({"uid": uid, "rights": rights})
        for uid, rights in d["users"].items():
            res["users"].append({"uid": uid, "rights": rights})
        self._log_debug("dict_process_in_result:\n%s" % res)
        return res
