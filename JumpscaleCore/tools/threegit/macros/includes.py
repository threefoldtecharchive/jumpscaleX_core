def includes(doc, path, title=3, **args):
    j = doc.docsite._j

    spath = j.sal.fs.processPathForDoubleDots(j.sal.fs.joinPaths(j.sal.fs.getDirName(doc.path), path))
    if not j.sal.fs.exists(spath, followlinks=True):
        doc.raiseError("Cannot find path for macro includes:%s" % spath)

    docNames = [j.sal.fs.getBaseName(item)[:-3] for item in j.sal.fs.listFilesInDir(spath, filter="*.md")]
    docNames = [j.sal.fs.joinPaths(path, name) for name in docNames]
    docNames.sort()

    titleprefix = "#" * title

    out = ""
    for docName in docNames:
        doc2 = doc.docsite.doc_get(docName, die=False)
        if doc2 == None:
            msg = "cannot execute macro includes, could not find doc:\n%s" % docName
            doc.raiseError(msg)
            return "```\n%s\n```\n" % msg
        out += "%s %s\n\n" % (titleprefix, doc2.title or docName)
        out += "%s\n\n" % doc2.markdown_source.rstrip("\n")

    return out
