def dot(doc, **kwargs):

    j = doc.docsite._j

    content = kwargs.get("content", "")
    if content.strip() == "":
        raise j.exceptions.Base("no content given for dot macro for:%s" % doc)

    md5 = j.data.hash.md5_string(content)
    md5 = bytes(md5.encode()).decode()
    name = "graph_%s" % md5
    name_cached = j.core.db.get("docsite:dot:%s" % name)

    link_src = "![%s.png](%s.png)" % (name, name)

    if name_cached != name:
        path = j.sal.fs.getTmpFilePath()
        j.sal.fs.writeFile(filename=path, contents=content)
        dest = j.sal.fs.joinPaths(j.sal.fs.getDirName(doc.path), "%s.png" % name)
        j.sal.process.execute("dot '%s' -Tpng > '%s'" % (path, dest))
        j.sal.fs.remove(path)
        j.sal.fs.copyFile(dest, "%s.png" % name)
        j.core.db.set("docsite:dot:%s" % name, md5)

    doc.link_add(link_src)

    return link_src
