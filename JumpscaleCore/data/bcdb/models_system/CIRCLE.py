from Jumpscale import j


class CIRCLE(j.data.bcdb._BCDBModelClass):
    def _schema_get(self):
        return j.data.schema.get_from_url("jumpscale.bcdb.circle.2")

    def userids_get(self):
        """
        will recursive get all users ids which are in circle & return as list of id's of users
        :param id:
        :return:
        """
        if not id in self._circles:
            users = []
            gr = self.model_circle.get(id)
            if gr:
                for userid in gr.users:
                    if userid not in users:
                        users.append(userid)
                for gid in gr.circles:
                    gr2 = self.model_circle.get(id)
                    if gr2:
                        for userid2 in gr2.users:
                            if userid2 not in users:
                                users.append(userid2)
            self._circles[id] = users
        return self._circles[id]
