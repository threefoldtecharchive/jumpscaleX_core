from Jumpscale import j
from JumpscaleLibs.tools.googleslides.slides2html.google_links_utils import get_presentation_id


EXPORT_TMP_DIR = "/tmp"
CRED_FILE_PATH = j.core.tools.text_replace("{DIR_BASE}/var/cred.json")


def gslide(doc, **kwargs):
    presentations = []
    for key in kwargs:
        if key.startswith("presentation"):
            presentations.append(kwargs[key])

    output = "```gslide\n"
    for pres in presentations:
        if "width" in kwargs and "height" in kwargs:
            j.tools.googleslides.export(
                pres,
                credfile=CRED_FILE_PATH,
                serviceaccount=True,
                websitedir=EXPORT_TMP_DIR,
                resize=(int(kwargs["width"]), int(kwargs["height"])),
            )
        else:
            j.tools.googleslides.export(pres, credfile=CRED_FILE_PATH, serviceaccount=True, websitedir=EXPORT_TMP_DIR)
        pres_id = get_presentation_id(pres)
        source = j.sal.fs.joinPaths(EXPORT_TMP_DIR, pres_id)
        dest = j.sal.fs.joinPaths(doc.docsite.outpath, pres_id)
        if j.sal.fs.exists(dest):
            j.sal.fs.remove(dest)
        j.sal.fs.moveDir(source, dest)

        files = [
            j.sal.fs.getBaseName(x)
            for x in j.sal.fs.listFilesInDir(dest)
            if x.endswith("png") and "_" in x and "background_" not in x
        ]

        files.sort(key=lambda k: int(k.split("_")[0]))
        for p in files:
            dirbasename = j.sal.fs.getBaseName(dest)
            image_tag = '<img src="./{docsite_name}/{dirbasename}/{p}" alt="{p}" />'.format(
                docsite_name=doc.docsite.name, dirbasename=dirbasename, p=p
            )
            output += """
            <section>
               <div class="slide-image">
                   {image}

               </div>
            </section>""".format(
                image=image_tag
            )
    output += "\n```"
    return output
