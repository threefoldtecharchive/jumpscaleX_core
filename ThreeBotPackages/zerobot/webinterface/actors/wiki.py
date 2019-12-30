from Jumpscale import j


class wiki(j.baseclasses.threebot_actor):

    # REMARK: was query before
    def find(self, name, text, schema_out=None, user_session=None):
        """
        ```in
        name = "" (S)
        text = "" (S)
        ```
        ```out
        res = (LS)
        ```
        :param name: Docsite name
        :param text: text to search for in all files
        :return:
        """
        out = schema_out.new()
        res = []
        try:
            res = j.sal.bcdbfs.search(text, location="/docsites/{}".format(name))
        except Exception as e:
            # TODO: check when sonic and bcdb are out of sync.
            print(e)
        out.res = res
        return out
