from Jumpscale import j

STATIC_DIR = "/sandbox/var/gdrive/static"


class gdrive(j.baseclasses.threebot_actor):
    def file_get(self, doctype, guid1, guid2, schema_out=None, user_session=None):
        """
        ```in
        doctype = "" (S)
        guid1 = (S)
        guid2 = "" (S)
        ```
        ```out
        res = (S)
        ```
        :param collection:
        :param bucket:
        :param text:
        :return:
        """

        doctypes_map = {"document": "drive", "spreadsheets": "drive", "presentation": "drive", "slide": "slides"}
        cl = j.clients.gdrive.get("gdrive_macro_client", credfile="/sandbox/var/cred.json")

        out = schema_out.new()

        if not doctype in doctypes_map:
            raise j.exceptions.Input("invalid type")

        service_name = doctypes_map[doctype]
        if doctype in ["document", "spreadsheets", "presentation"]:
            path = j.sal.fs.joinPaths(STATIC_DIR, doctype, "{}.pdf".format(guid1))
            cl.exportFile(guid1, destpath=path, service_name=service_name, service_version="v3")

            out.res = "/gdrive_static/{}/{}.pdf".format(doctype, guid1)
        elif doctype == "slide":
            path = j.sal.fs.joinPaths(STATIC_DIR, doctype)
            cl.exportSlides(guid1, path)
            if j.sal.fs.exists("{}/{}/{}.png".format(path, guid1, guid2), followlinks=True):
                out.res = "/gdrive_static/slide/{}/{}.png".format(guid1, guid2)
            else:
                meta = cl.get_presentation_meta("{}/presentations.meta.json".format(path), guid1)
                guid2 = meta[guid2]
                guid2 = guid2.split("_", maxsplit=1)[1]  # remove the 0x_ part from the file name
                out.res = "/gdrive_static/slide/{}/{}".format(guid1, guid2)

        return out
