def _file_process(j, content, start="", end="", paragraph=False, docstring=""):
    """
    finds a part of a file which matches start argument
    :param j: to have the jumpscale tools
    :param content: on what we are looking for
    :param start: when line starts with $start it gets included in result
    :param end: if specified (is optional), then will go untill end found (match any part of line)
    :param paragraph: if True, will look for end of paragraph and return that part
    :param docstring: when this is used then start/end/paragraph will not be used, this one is to the docstring of a class or method
                    the docstring is the name of the method or class
    :return:
    """
    if start == "" and end == "" and docstring == "":
        return content

    if start is not "":
        start = start.lower()
        out = ""
        state = "START"
        for line in content.split("\n"):
            lstrip = line.strip().lower()

            if lstrip.startswith(start):
                state = "FOUND"
                out += "%s\n" % line
                continue
            if state == "FOUND":
                if paragraph:
                    # means looking for paragraph
                    if len(line) > 0 and line[0] != " ":
                        return out
                out += "%s\n" % line
                if end != "" and lstrip.find(end.lower()) != -1:
                    return out
    elif docstring is not "":
        # now find the docstring attached to class or method
        docstring = docstring.lower()
        out = ""
        state = "START"

        for line in content.split("\n"):
            lstrip = line.strip().lower()
            lstrip = lstrip.replace('"', "`")
            lstrip = lstrip.replace("'", "`")
            if lstrip.startswith("def %s" % docstring) or lstrip.startswith("class %s" % docstring):
                state = "FOUND"
                continue
            if state == "FOUND":
                if lstrip.startswith("```"):
                    state = "FOUND2"
                    continue
            if state == "FOUND2":
                if lstrip.startswith("```"):
                    out = j.core.text.strip(out).replace("\n\n\n", "\n\n")
                    return out
                out += "%s\n" % line

    else:
        raise j.exceptions.Base("start of docstring needs to be specified")
    return out


def include_original(
    doc, name="test5", docsite="", repo="", start="", end="", paragraph=False, codeblock=False, docstring="", **args
):
    """

    :param name: name of the document to look for (will always be made lowercase)
    :param docsite: name of the docsite
    :param repo: url of the repo, if url given then will checkout the required content from a git repo
    :param start: will walk over the content of the file specified (name) and only include starting from line where the start argument is found
    :param end: will match till end
    :param paragraph: if True then will include from start till next line is found which is at same prefix (basically taking out a paragraph)
    :param codeblock: will put the found result in a codeblock if True
    :param docstring: will look for def $name or class $name and include the docstring directly specified after it as markdown
    :return:
    """
    name = name.lower()
    j = doc.docsite._j

    if repo != "":
        path = j.clients.git.getContentPathFromURLorPath(repo)
        key = j.data.hash.md5_string("macro_include_%s_%s" % (repo, name))

        def do(path="", name="", start="", end="", paragraph=False, docstring=""):
            tofind = name.lower().replace("\\", "/").replace("//", "/")
            ext = j.sal.fs.getFileExtension(name)
            extlower = ext.lower()
            res = []
            for item in j.sal.fs.listFilesInDir(path, recursive=True, followSymlinks=False, listSymlinks=False):
                if item.lower().find(tofind) != -1:
                    res.append(item)
            if len(res) > 1:
                raise j.exceptions.Base("found more than 1 document for:%s %s" % (path, name))
            if len(res) == 0:
                raise j.exceptions.Base("could not find document in repo:%s name:%s" % (path, name))
            content = j.sal.fs.readFile(res[0])
            content = j.core.text.strip(content)
            content2 = _file_process(
                j=j, content=content, start=start, end=end, paragraph=paragraph, docstring=docstring
            )

            if extlower in ["", "md"]:
                return content2
            else:
                if extlower in ["py"]:
                    lang = "python"
                elif extlower in ["toml"]:
                    lang = "toml"
                elif extlower in ["json"]:
                    lang = "json"
                elif extlower in ["yaml"]:
                    lang = "yaml"
                elif extlower in ["txt"]:
                    lang = "txt"
                elif extlower in ["bash", "sh"]:
                    lang = "bash"
                else:
                    raise j.exceptions.Base("did not find extension to define which code language")

                content3 = content2.replace("```", "'''")
                content4 = "```%s\n\n%s\n\n```\n\n" % (lang, content3)
            return content4

        content = j.tools.markdowndocs._cache.get(
            key,
            method=do,
            expire=600,
            refresh=True,
            path=path,
            name=name,
            start=start,
            end=end,
            docstring=docstring,
            paragraph=paragraph,
        )
        return content

    if name.find(":") == -1:
        doc = doc.docsite.doc_get(name, die=False)
        if doc == None:
            # walk over all docsites
            res = []
            for key, ds in j.tools.markdowndocs.docsites.items():
                doc = ds.doc_get(name, die=False)
                if doc != None:
                    res.append(doc)
            if len(res) == 1:
                doc = res[0]
            else:
                # did not find or more than 1
                doc = None

        if doc != None:

            newcontent = _file_process(
                j=j, content=doc.markdown, start=start, end=end, paragraph=paragraph, docstring=docstring
            )
        else:
            raise j.exceptions.Base("ERROR: COULD NOT INCLUDE:%s (not found)" % name)

    else:
        docsiteName, name = name.split(":")
        docsite = j.tools.markdowndocs.docsite_get(docsiteName)
        doc = docsite.doc_get(name, die=False)
        if doc != None:

            newcontent = _file_process(
                j=j, content=doc.markdown, start=start, end=end, paragraph=paragraph, docstring=docstring
            )
        else:
            raise j.exceptions.Base("ERROR: COULD NOT INCLUDE:%s:%s (not found)" % (docsiteName, name))

    return newcontent
