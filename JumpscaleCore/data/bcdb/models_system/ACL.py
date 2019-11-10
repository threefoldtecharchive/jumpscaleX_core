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

    def rights_set(self, acl, userids=None, circleids=None, rights=None):
        for userid in userids:
            name = f"user_{acl.name}_{userid}"
            for acl_user in acl.users:
                if acl_user.uid == userid:
                    user = acl_user
                    break
            else:
                user = self.acl_users_model.new(name=name)
                user.uid = userid
                new = True

            user.rights.extend(rights)
            user.save()
            if new:
                acl.users.append(user)

        while circleids:
            circleid = circleids.pop()
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

            circle.rights.extend(rights)
            circle.save()
            if new:
                acl.circles.append(circle)
            subcircles = self.circles_model.get(circleid).circle_members
            if subcircles:
                circleids.extend(subcircles)

        acl.md5 = j.data.hash.md5_string(acl._data)
        acl.save()

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

    def _acl_search_user(self, acl, user_id):
        """
        serach in users inside acl object or in sub circles
        :param acl:
        :return:
        """
        for user in acl.users:
            if user.uid == user_id:
                return user

        self._acl_search_circles(acl.circles, user_id, is_user=True)

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

    # def _methods_add(self, obj):
    #     """
    #     what does this do?
    #     :param self:
    #     :param obj:
    #     :return:
    #     """
    #     obj.rights_set = types.MethodType(self.rights_set, obj)
    #     obj.rights_check = types.MethodType(self.rights_check, obj)
    #
    #     return obj

    # def _dict_process_out(self, d):
    #     res = {}
    #     self._log_debug("dict_process_out:\n%s" % d)
    #     for circle in d["circles"]:
    #         if circle.get("cid"):
    #             r = self.circle.get_by_name("circle_%s" % circle["cid"])
    #             r = "".join(r.rights)
    #             acl_circle = self.circle.get_by_name("circle_%s" % circle["cid"])
    #             res[acl_circle.cid] = r  # as string
    #     d["circles"] = res
    #     res = {}
    #     for user in d["users"]:
    #         if user.get("uid"):
    #             r = self.user.get_by_name("user_%s" % user["uid"])
    #             r = "".join(r.rights)
    #             acl_user = self.user.get_by_name("user_%s" % user["uid"])
    #             res[acl_user.uid] = r  # as string
    #     d["users"] = res
    #     return d

    # def _dict_process_in(self, d):
    #     res = {}
    #     res["hash"] = d["hash"]
    #     res["circles"] = []
    #     res["users"] = []
    #     for cid, rights in d["circles"].items():
    #         res["circles"].append({"cid": cid, "rights": rights})
    #     for uid, rights in d["users"].items():
    #         res["users"].append({"uid": uid, "rights": rights})
    #     self._log_debug("dict_process_in_result:\n%s" % res)
    #     return res
