from Jumpscale import j


class sonic(j.baseclasses.object):
    def query(self, name, text, schema_out=None, user_session=None):
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
        out.res = j.sal.bcdbfs.search(text, location="/docsites/{}".format(name))
        return out
