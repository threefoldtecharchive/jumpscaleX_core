import re
from Jumpscale import j

JSBASE = j.baseclasses.object


class RegexTemplates_FindLines(j.baseclasses.object):
    """
    regexexamples which find lines
    """

    # TODO: for all methods do input checking  (id:20)
    def __init__(self):
        JSBASE.__init__(self)

    def findCommentlines(self):
        return "^( *#).*"

    def findClasslines(self):
        return "^class .*"

    def findDeflines(self):
        return "^def .*"


class Empty(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)


class RegexMatches(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)
        self.matches = []

    def addMatch(self, match):
        if match is not None or match != "":
            rm = RegexMatch()
            rm.start = match.start()
            rm.end = match.end()
            rm.founditem = match.group()
            rm.foundSubitems = match.groups()
        self.matches.append(rm)

    def __str__(self):
        out = ""
        for match in self.matches:
            out = out + match.__str__()
        return out

    def __repr__(self):
        return self.__str__()


class RegexMatch(j.baseclasses.object):
    def __init__(self):
        self.start = 0
        self.end = 0
        self.founditem = ""
        self.foundSubitems = None

    def __str__(self):
        out = "%s start:%s end:%s\n" % (self.founditem, self.start, self.end)
        return out

    def __repr__(self):
        return self.__str__()


class RegexTools(j.baseclasses.object):
    # TODO: doe some propper error handling with re, now obscure errors  (id:21)
    __jslocation__ = "j.data.regex"

    def _init(self, **kwargs):

        self.templates = Empty()
        self.templates.lines = RegexTemplates_FindLines()

    def findHtmlElement(self, subject, tofind, path, dieIfNotFound=True):
        match = re.search(r"< *%s *>" % tofind, subject, re.IGNORECASE)
        if match:
            result = match.group()
            return result
        else:
            if dieIfNotFound:
                raise j.exceptions.RuntimeError("Could not find %s in htmldoc %s" % (tofind, path))
            else:
                return ""

    def findHtmlBlock(self, subject, tofind, path, dieIfNotFound=True):
        """
        only find 1 block ideal to find e.g. body & header of html doc
        """
        found = self.findHtmlElement(subject, tofind, path, dieIfNotFound)
        if found == "":
            return ""
        subject = subject.split(found)[1]  # remove tofind pre part
        # now we need to die because first element found
        found = self.findHtmlElement(subject, "/%s" % tofind, path, dieIfNotFound=True)
        result, post = subject.split(found)  # look for end
        return result

    def match(self, pattern, text):
        """
        search if there is at least 1 match
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do .codetools.regex.match when " "pattern or text parameter is empty"
            )
        # self._log_debug("Regextools: pattern:%s in text:%s" % (pattern,text),5)
        # print "Regextools: pattern:%s in text:%s" % (pattern,text)
        pattern = self._patternFix(pattern)
        result = re.findall(pattern, text)
        if len(result) > 0:
            return True
        else:
            return False

    def matchContent(self, path, contentRegexIncludes=[], contentRegexExcludes=[]):
        content = j.sal.fs.readFile(path)
        return self.matchMultiple(patterns=contentRegexIncludes, text=content) and not self.matchMultiple(
            patterns=contentRegexExcludes, text=content
        )

    def matchPath(path, regexIncludes=[], regexExcludes=[]):
        return self.matchMultiple(patterns=regexIncludes, text=path) and not self.matchMultiple(
            patterns=regexExcludes, text=path
        )

    def matchMultiple(self, patterns, text):
        """
        see if any patterns matched
        if patterns=[] then will return False
        """
        if patterns == "":
            raise j.exceptions.RuntimeError("Cannot do .codetools.regex.matchMultiple when " "pattern is empty")
        if text == "":
            return False
        if type(patterns).__name__ != "list":
            raise j.exceptions.RuntimeError("patterns has to be of type list []")
        if patterns == []:
            return False

        for pattern in patterns:
            pattern = self._patternFix(pattern)
            if self.match(pattern, text):
                return True
        return False

    def _patternFix(self, pattern):
        if pattern.find("(?m)") == -1:
            pattern = "%s%s" % ("(?m)", pattern)
        return pattern

    def replace(self, regexFind, regexFindsubsetToReplace, replaceWith, text):
        """
        Search for regexFind in text and if found, replace the subset
        regexFindsubsetToReplace of regexFind with replacewith and
        returns the new text
        Example:
            replace("Q-Layer Server", "Server", "Computer",
                            "This is a Q-Layer Server")
            will return "This is a Q-Layer Computer"
        @param regexFind: String to search for, can be a regular expression
        @param regexFindsubsetToReplace: The subset within regexFind
                that you want to replace
        @param replacewith: The replacement
        @param text: Text where you want to search and replace
        """
        if not regexFind or not regexFindsubsetToReplace or not text:
            raise j.exceptions.RuntimeError(
                "Cannot do .codetools.regex.replace when " "any of the four variables is empty."
            )
        if regexFind.find(regexFindsubsetToReplace) == -1:
            raise j.exceptions.RuntimeError(
                "regexFindsubsetToReplace must be part or "
                'all of regexFind "ex: regexFind="Some example text", '
                'regexFindsubsetToReplace="example"'
            )
        matches = self.findAll(regexFind, text)
        if matches:
            finalReplaceWith = re.sub(regexFindsubsetToReplace, replaceWith, matches[0])
            text = re.sub(self._patternFix(regexFind), finalReplaceWith, text)

        return text

    def findOne(self, pattern, text, flags=0):
        """ Searches for a one match only on pattern inside text,
            will throw a RuntimeError if more than one match found
            @param pattern: Regex pattern to search for
            @param text: Text to search in
        """
        if not pattern or not text:
            raise j.exceptions.RuntimeError(
                "Cannot do .codetools.regex.findOne when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)
        result = re.finditer(pattern, text, flags)
        finalResult = list()
        for item in result:
            finalResult.append(item.group())

        if len(finalResult) > 1:
            raise j.exceptions.RuntimeError("found more than 1 result of regex %s in text %s" % (pattern, text))
        if len(finalResult) == 1:
            return finalResult[0]
        return ""

    def findAll(self, pattern, text, flags=0):
        """ Search all matches of pattern in text and returns an array
            @param pattern: Regex pattern to search for
            @param text: Text to search in
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do .codetools.regex.findAll when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)
        results = re.finditer(pattern, text, flags)
        matches = list()
        if results:
            matches = [x.group() for x in results]
        return matches

    def getRegexMatches(self, pattern, text, flags=0):
        """
        match all occurences and find start and stop in text
        return RegexMatches  (is array of RegexMatch)
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do j.data.regex.getRegexMatches when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)
        rm = RegexMatches()
        for match in re.finditer(pattern, text, flags):
            rm.addMatch(match)
        return rm

    def yieldRegexMatches(self, pattern, text, flags=0):
        """The same as getRegexMatches but instead of returning a
            list that contains all matches it uses yield to return
                a generator object
            which would improve the performance of the search function.
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do j.data.regex.getRegexMatches when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)

        for match in re.finditer(pattern, text, flags):
            rm = RegexMatch()
            rm.start = match.start()
            rm.end = match.end()
            rm.founditem = match.group()
            rm.foundSubitems = match.groups()
            yield rm

    def matchAllText(self, pattern, text):
        result = self.getRegexMatch(pattern, text)
        if result is None:
            return False
        if result.founditem.strip() != text.strip():
            return False

    def getRegexMatch(self, pattern, text, flags=0):
        """ find the first match in the string that matches the pattern.
            @return RegexMatch object, or None if didn't match any.
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do j.data.regex.getRegexMatches when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)
        match = re.match(pattern, text, flags)
        if match:
            rm = RegexMatch()
            rm.start = match.start()
            rm.end = match.end()
            rm.founditem = match.group()
            rm.foundSubitems = match.groups()
            return rm
        else:
            return None  # no match

    def removeLines(self, pattern, text):
        """ remove lines based on pattern
        """
        if pattern == "" or text == "":
            raise j.exceptions.RuntimeError(
                "Cannot do j.data.regex.removeLines when " "pattern or text parameter is empty"
            )
        pattern = self._patternFix(pattern)
        return self.processLines(text, excludes=[pattern])

    def processLines(self, text, includes="", excludes=""):
        """ includes happens first
            excludes last
            both are arrays
        """
        if includes == "":
            includes = [".*"]  # match all
        if excludes == "":
            excludes = []  # match none

        lines = text.split("\n")
        out = ""
        for line in lines:
            if self.matchMultiple(includes, line) and not self.matchMultiple(excludes, line):
                out = "%s%s\n" % (out, line)
        return out

    def replaceLines(self, replaceFunction, arg, text, includes="", excludes=""):
        """ includes happens first (includes of regexes eg @process.*
            matches full line starting with @process)
            excludes last
            both are arrays
            replace the matched line with line being processed by
            the functionreplaceFunction(arg,lineWhichMatches)
            the replace function has 2 params, argument & the matching line
        """
        if includes == "":
            includes = [".*"]  # match all
        if excludes == "":
            excludes = []  # match none

        lines = text.split("\n")
        out = ""
        for line in lines:
            if self.matchMultiple(includes, line) and not self.matchMultiple(excludes, line):
                line = replaceFunction(arg, line)
            out = "%s%s\n" % (out, line)
        if out[-2:] == "\n\n":
            out = out[:-1]
        return out

    def findLine(self, regex, text):
        """ returns line when found
            @param regex is what we are looking for
            @param text, we are looking into
        """

        return self.processLines(text, includes=[self._patternFix(regex)], excludes="")

    def getINIAlikeVariableFromText(self, variableName, text, isArray=False):
        """ e.g. in text
            '
            test= something
            testarray = 1,2,4,5
            '
            getINIAlikeVariable("test",text) will return 'something'
            @isArray when True and , in result will make array out of
            getINIAlikeVariable("testarray",text,True) will return [1,2,4,5]
        """
        line = self.findLine("^%s *=" % variableName, text)
        if line != "":
            val = line.split("=")[1].strip()
            if isArray:
                splitted = val.split(",")
                if len(splitted) > 0:
                    splitted = [item.strip() for item in splitted]
                    return splitted
                else:
                    return [val]
            else:
                return val
        return ""

    def extractFirstFoundBlock(
        self,
        text,
        blockStartPatterns,
        blockStartPatternsNegative=[],
        blockStopPatterns=[],
        blockStopPatternsNegative=[],
        linesIncludePatterns=[".*"],
        linesExcludePatterns=[],
        includeMatchingLine=True,
    ):
        result = self.extractBlocks(
            text,
            blockStartPatterns,
            blockStartPatternsNegative,
            blockStopPatterns,
            blockStopPatternsNegative,
            linesIncludePatterns,
            linesExcludePatterns,
            includeMatchingLine,
        )
        if len(result) > 0:
            return result[0]
        else:
            return ""

    def extractBlocks(
        self,
        text,
        blockStartPatterns=[".*"],
        blockStartPatternsNegative=[],
        blockStopPatterns=[],
        blockStopPatternsNegative=[],
        linesIncludePatterns=[".*"],
        linesExcludePatterns=[],
        includeMatchingLine=True,
    ):
        """ look for blocks starting with line which matches one of patterns
            in blockStartPatterns and not matching one of patterns in
            blockStartPatternsNegative
            block will stop when line found which matches one of patterns
            in blockStopPatterns and not in blockStopPatternsNegative or
            when next match for start is found
            in block lines matching linesIncludePatterns will be kept
            and reverse for linesExcludePatterns
            example pattern: '^class ' looks for class at beginning
            of line with space behind
        """
        # check types of input
        if (
            not isinstance(blockStartPatterns, list)
            or not isinstance(blockStartPatternsNegative, list)
            or not isinstance(blockStopPatterns, list)
            or not isinstance(blockStopPatternsNegative, list)
            or not isinstance(linesIncludePatterns, list)
            or not isinstance(linesExcludePatterns, list)
        ):
            raise j.exceptions.RuntimeError(
                "Blockstartpatterns, blockStartPatternsNegative,"
                "blockStopPatterns, blockStopPatternsNegative,"
                "linesIncludePatterns, linesExcludePatterns "
                "all have to be of type list"
            )

        state = "scan"
        lines = text.split("\n")
        line = ""
        result = []
        for t in range(len(lines)):
            line = lines[t]
            # print "\nPROCESS: %s,%s state:%s line:%s" % \
            #               (t,len(lines)-1,state,line)
            emptyLine = not line
            # XXX this code is an absolute mess.  completely unreadable.
            # break it down into separate statements (that fit onto 80 chars)
            # and add unit tests
            addLine = (
                self.matchMultiple(linesIncludePatterns, line) and not self.matchMultiple(linesExcludePatterns, line)
            ) or emptyLine
            if state == "foundblock" and (
                t == len(lines) - 1
                or (
                    self.matchMultiple(blockStopPatterns, line)
                    or (
                        self.matchMultiple(blockStartPatterns, line)
                        and not self.matchMultiple(blockStartPatternsNegative, line)
                    )
                    or (len(blockStopPatternsNegative) > 0 and not self.matchMultiple(blockStopPatternsNegative, line))
                )
            ):

                # new potential block found or end of file
                result.append(block)  # add to results line
                if t == len(lines) - 1:
                    state = "endoffile"
                    if addLine:
                        block = "%s%s\n" % (block, line)
                else:
                    # have to go back to scanning
                    state = "scan"
                    if blockStartPatterns == blockStopPatterns:
                        # otherwise we would start match again
                        if t < len(lines):
                            t = t + 1
                            line = lines[t]
                        else:
                            line = ""

            if state == "foundblock":
                # print "foundblock %s" % \
                #               self.matchMultiple(linesIncludePatterns,line)
                if addLine:
                    block = "%s%s\n" % (block, line)

            if (
                state == "scan"
                and self.matchMultiple(blockStartPatterns, line)
                and not self.matchMultiple(blockStartPatternsNegative, line)
            ):
                # found beginning of block
                state = "foundblock"
                blockstartline = t
                block = ""
                if includeMatchingLine:
                    if addLine:
                        block = line + "\n"

        return result

    def test(self):
        # content = j.sal.fs.readFile("examplecontent1.txt")
        # print(self.getClassName("class iets(test):"))
        content = "class iets(test):"
        # find all occurences of class and find positions
        regexmatches = j.data.regex.getRegexMatches(r"(?m)(?<=^class )[ A-Za-z0-9_\-]*\b", content)
        return regexmatches
