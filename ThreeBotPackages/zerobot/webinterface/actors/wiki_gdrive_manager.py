from Jumpscale import j

# get gdrive client so google api dependency is installed
cl = j.clients.gdrive.get("gdrive_macro_client", credfile=j.core.tools.text_replace("{DIR_BASE}/var/cred.json"))

from googleapiclient.errors import HttpError as GoogleApiHTTPError


STATIC_DIR = j.core.tools.text_replace("{DIR_BASE}/var/gdrive/static")
doctypes_map = {"document": "drive", "spreadsheets": "drive", "presentation": "drive", "slide": "slides"}


class wiki_gdrive_manager(j.baseclasses.threebot_actor):
    @j.baseclasses.actor_method
    def file_get(self, doctype, guid1, guid2, schema_out=None, user_session=None):
        """
        ```in
        doctype = "" (S)
        guid1 = (S)
        guid2 = "" (S)
        ```
        ```out
        res = "" (S)
        error_message = "" (S)
        error_code = 0 (I)
        ```
        :param collection:
        :param bucket:
        :param text:
        :return:
        """

        out = schema_out.new()

        if not doctype in doctypes_map:
            out.error_code = -1
            allowed_types = ", ".join(doctypes_map.keys())
            out.error_message = f"invalid document type of '{doctype}', allowed types are {allowed_types}."
            return out

        if not j.sal.fs.exists(cl.credfile):
            out.error_code = 400
            out.error_message = "service credential file is not found"
            return out

        service_name = doctypes_map[doctype]
        try:
            parent_dir = j.sal.fs.joinPaths(STATIC_DIR, doctype)
            if not j.sal.fs.exists(parent_dir):
                j.sal.fs.createDir(parent_dir)

            if doctype in ["document", "spreadsheets", "presentation"]:
                path = j.sal.fs.joinPaths(parent_dir, "{}.pdf".format(guid1))
                cl.exportFile(guid1, destpath=path, service_name=service_name, service_version="v3")
                out.res = "/gdrive_static/{}/{}.pdf".format(doctype, guid1)
            elif doctype == "slide":
                cl.exportSlides(guid1, parent_dir)
                if j.sal.fs.exists("{}/{}/{}.png".format(parent_dir, guid1, guid2), followlinks=True):
                    out.res = "/gdrive_static/slide/{}/{}.png".format(guid1, guid2)
                else:
                    meta = cl.get_presentation_meta("{}/presentations.meta.json".format(parent_dir), guid1)
                    if guid2 in meta:
                        guid2 = meta[guid2]
                        guid2 = guid2.split("_", maxsplit=1)[1]  # remove the 0x_ part from the file name
                        out.res = "/gdrive_static/slide/{}/{}".format(guid1, guid2)
        except GoogleApiHTTPError as api_http_error:
            error = j.data.serializers.json.loads(api_http_error.content)["error"]
            out.error_code = error["code"]
            out.error_message = error["message"]
        return out
