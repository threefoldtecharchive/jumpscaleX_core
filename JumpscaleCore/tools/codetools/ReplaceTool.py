from Jumpscale import j
import re
import random

JSBASE = j.baseclasses.object

JSBASE = j.baseclasses.object


class Synonym(j.baseclasses.object):
    def __init__(self, name="", replaceWith="", simpleSearch="", replaceExclude=""):
        """
        @param name: Name of the sysnoym
        @param replaceWith: The replacement of simpleSearch
        @param simpleSearch: Search string that'll be replaced with replaceWith
        @defSynonym: If True then this is a definition synonym, which can be used in spectools
        """
        JSBASE.__init__(self)
        self.simpleSearch = simpleSearch
        self.regexFind = ""
        self.regexFindForReplace = ""
        self.name = name
        self.replaceWith = replaceWith
        self.replaceExclude = replaceExclude
        self._markers = dict()
        if simpleSearch != "":
            search = simpleSearch.replace("?", "[ -_]?")  # match " " or "-" or "_"  one or 0 time
            if addConfluenceLinkTags:
                bracketMatchStart = "(\[ *|)"
                bracketMatchStop = "( *\]|)"
            else:
                bracketMatchStart = ""
                bracketMatchStop = ""
            self.regexFind = r"(?i)%s\b%s\b%s" % (bracketMatchStart, search.lower(), bracketMatchStop)
            # self.regexFind=r"%s\b%s\b%s" % (bracketMatchStart,search.lower(),bracketMatchStop)
            self.regexFindForReplace = self.regexFind

    def setRegexSearch(self, regexFind, regexFindForReplace):
        self.regexFind = regexFind
        if regexFindForReplace == "":
            regexFindForReplace = regexFind
        self.regexFindForReplace = regexFindForReplace
        self.simpleSearch = ""

    def replace(self, text):
        if self.replaceExclude:
            # Check for any def tag that contains name "e.g: [ Q-Layer ]", remove them and put markers in place
            text = self._replaceDefsWithMarkers(text)
        text = j.data.regex.replace(
            regexFind=self.regexFind,
            regexFindsubsetToReplace=self.regexFindForReplace,
            replaceWith=self.replaceWith,
            text=text,
        )
        if self.replaceExclude:
            # Remove the markers and put the original def tags back
            text = self._replaceMarkersWithDefs(text)
        return text

    def _replaceDefsWithMarkers(self, text):
        """
        Search for any def tags that contains the name of this synonym  "e.g [Q-layer]" in text and replace that with a special marker. Also it stores markers and replaced string into the dict _markers
        """
        # patterns you don't want to be replaced
        pat = self.replaceExclude

        matches = j.data.regex.findAll(pat, text)

        for match in matches:
            mark = "$$MARKER$$%s$$" % random.randint(0, 1000)
            self._markers[mark] = match
            match = re.escape(match)
            text = j.data.regex.replace(regexFind=match, regexFindsubsetToReplace=match, replaceWith=mark, text=text)
        return text

    def _replaceMarkersWithDefs(self, text):
        """
        Removes markers out of text and puts the original strings back
        """
        for marker, replacement in list(self._markers.items()):
            marker = re.escape(marker)
            text = j.data.regex.replace(
                regexFind=marker, regexFindsubsetToReplace=marker, replaceWith=replacement, text=text
            )
        return text

    def __str__(self):
        out = "name:%s simple:%s regex:%s regereplace:%s replacewith:%s\n" % (
            self.name,
            self.simpleSearch,
            self.regexFind,
            self.regexFindForReplace,
            self.replaceWith,
        )
        return out

    def __repr__(self):
        return self.__str__()


class ReplaceTool(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)
        self.synonyms = []  # array Synonym()

    def synonymsPrint(self):
        for syn in self.synonyms:
            self._log_debug(syn)

    def synonymAdd(
        self, name="", simpleSearch="", regexFind="", regexFindForReplace="", replaceWith="", replaceExclude=""
    ):
        """
        Adds a new synonym to this replacer
        @param name: Synonym name (optional)
        @param simpleSearch: Search text for sysnonym, if you supply this, then the synonym will automatically generate a matching regex pattern that'll be used to search for this string, if you want to specificy the regex explicitly then use regexFind instead.
        @param regexFind: Provide this regex only if you didn't provide simpleSearch, it represents the regex that'll be used in search for this synonym . It overrides the default synonym search pattern
        @param regexFindForReplace: The subset within regexFind that'll be replaced for this synonym
        """
        synonym = Synonym(name, replaceWith, simpleSearch, replaceExclude)
        if regexFind:
            synonym.setRegexSearch(regexFind, regexFindForReplace)
        self.synonyms.append(synonym)

    def reset(self):
        self.synonyms = []

    def synonymsAddFromFile(self, path, addConfluenceLinkTags=False):
        """
        load synonym satements from a file in the following format
        [searchStatement]:[replaceto]
        or
        '[regexFind]':'[regexReplace]':replaceto
        note: delimiter is :
        note: '' around regex statements
        e.g.
        ******
        master?daemon:ApplicationServer
        application?server:ApplicationServer
        'application[ -_]+server':'application[ -_]+server':ApplicationServer
        '\[application[ -_]+server\]':'application[ -_]+server':ApplicationServer
        ******
        @param addConfluenceLinkTags id True then replaced items will be surrounded by [] (Boolean)
        """
        txt = j.sal.fs.readFile(path)
        for line in txt.split("\n"):
            line = line.strip()
            if line != "" and line.find(":") != -1:
                if j.data.regex.match("^'", line):
                    # found line which is regex format
                    splitted = line.split("'")
                    if len(splitted) != 4:
                        raise j.exceptions.RuntimeError(
                            "syntax error in synonym line (has to be 2 'regex' statements" % line
                        )
                    syn = Synonym(replaceWith=splitted[2])
                    syn.setRegexSearch(regexFind=splitted[0], regexFindForReplace=splitted[1])
                else:
                    find = line.split(":")[0]
                    replace = line.split(":")[1].strip()
                    syn = Synonym(replaceWith=replace, simpleSearch=find, addConfluenceLinkTags=addConfluenceLinkTags)
                self.synonyms.append(syn)

    # def removeConfluenceLinks(self, text):
    #     """
    #     find [...] and remove the [ and the ]
    #     TODO: 2  (id:19)
    #     """
    #     raise j.exceptions.RuntimeError("todo needs to be done, is not working now")

    #     def replaceinside(matchobj):
    #         match = matchobj.group()
    #         # we found a match now
    #         # self._log_debug "regex:%s match:%s replace:%s" % (searchitem[1],match,searchitem[2])
    #         if match.find("|") == -1:
    #             match = re.sub("( *\])|(\[ *)", "", match)
    #             toreplace = searchitem[2]
    #             searchregexReplace = searchitem[1]
    #             match = re.sub(searchregexReplace, toreplace, match)
    #             return match
    #         else:
    #             return match
    #     for searchitem in self.synonyms:
    #         #text = re.sub(searchitem[0],searchitem[1], text)
    #         text = re.sub(searchitem[0], replaceinside, text)
    #     return text

    def replace(self, text):
        for syn in self.synonyms:
            text = syn.replace(text)
        return text

    def replace_in_dir(self, path, recursive=False, filter=None):
        for item in j.sal.fs.listFilesInDir(path=path, recursive=recursive, filter=filter, followSymlinks=True):
            try:
                C = j.sal.fs.readFile(item)
            except Exception as e:
                if "codec can't" not in str(e):
                    raise j.exceptions.Base(e)
                C = ""
            if C == "":
                continue
            C2 = self.replace(C)
            if C != C2:
                self._log_debug("replaced %s in dir for: %s" % (item, path))
                j.sal.fs.writeFile(item, C2)

    # def replaceInConfluence(self, text):
    #     """
    #     @[..|.] will also be looked for and replaced
    #     """
    #     def replaceinside(matchobj):
    #         match = matchobj.group()
    #         # we found a match now
    #         # self._log_debug "regex:%s match:%s replace:%s" % (searchitem[1],match,searchitem[2])
    #         if match.find("|") == -1:
    #             match = re.sub("( *\])|(\[ *)", "", match)
    #             match = re.sub(syn.regexFind, syn.replaceWith, match)
    #             return match
    #         else:
    #             return match
    #     for syn in self.synonyms:
    #         # call function replaceinside when match
    #         text = re.sub(syn.regexFind, replaceinside, text)
    #     return text

    # def _addConfluenceLinkTags(self, word):
    #     """
    #     add [ & ] to word
    #     """
    #     if word.find("[") == -1 and word.find("]") == -1:
    #         word = "[%s]" % word
    #     return word
