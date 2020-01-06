from Jumpscale import j
from JumpscaleLibs.tools.googleslides.slides2html.google_links_utils import get_document_id


CRED_FILE_PATH = j.core.tools.text_replace("{DIR_BASE}/var/cred.json")


def markdown(doc, url, **kwargs):
    client = j.clients.gdrive.get(name="markdown_macro", credfile=CRED_FILE_PATH)
    discovery = client.service_get().files()

    output = ""
    file_id = get_document_id(url)
    if not file_id:
        raise j.exceptions.Value("invalid document url.")
    request = discovery.export(fileId=file_id, mimeType="text/plain")
    content = request.execute().decode(encoding="utf-8-sig")
    output += content

    output += ""
    return output
