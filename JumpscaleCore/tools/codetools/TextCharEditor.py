from Jumpscale import j

JSBASE = j.baseclasses.object


class TextCharEditor(j.baseclasses.object):
    """
    represents a piece of text but broken appart in blocks
    this one works on a char basis
    """

    def __init__(self, text, textfileeditor):
        JSBASE.__init__(self)
        text = text.replace("\t", "    ")
        text = text.replace("\r", "")
        self.chars = [[char, "", 0] for char in text]  # is the array of the text, each value = [char,blockname,blocknr]
        # self.charsBlocknames=[]  #position as in chars will have as value the blockname, if blockname=="" then not matched
        # self.charsBlocknrs=[]  #position as in chars will have as value the blocknr
        self._higestblocknr = {}  # key is name of block, the value is the last used blocknr
        self._textfileeditor = textfileeditor

    def save(self):
        self._textfileeditor.content = self.getText()
        self._textfileeditor.save()

    def getText(self):
        return "".join([char[0] for char in self.chars])

    def getNrChars(self):
        return len(self.chars)

    def existsBlock(self, blockname):
        return blockname in self._higestblocknr

    def getBlockNames(self):
        return list(self._higestblocknr.keys())

    def matchBlocksPattern(self, startpattern, stoppattern, blockname):
        """
        will look for startpattern, then scan for stoppattern
        will only work on text which is not part of known blocks yet
        example to find comments which are full line based startpattern='^[ \t]*%%'  stoppattern="\n"
        """
        result = j.data.regex.getRegexMatches(startpattern, self.getText())
        if len(result.matches) == 0:
            pass
        for match in result.matches:
            start = match.start
            textToInvestigate = string.join([char[0] for char in self.chars[match.start :]], "")
            result2 = j.data.regex.getRegexMatches(stoppattern, textToInvestigate)
            if len(result2.matches) == 0:
                raise j.exceptions.RuntimeError("could not find stoppattern %s" % stoppattern)
            end = result2.matches[0].end
            skip = False
            for pos in range(
                match.start, match.start + end
            ):  # scan first time if somewhere there is already a char part of a block
                if self.chars[pos][1] != "":
                    skip = True
                    # self._log_debug("Could not match the pattern because as part of result there was already another block found, posstart:%s posstop%s" % (match.start,match.start+end-1),5)
            blocknr = self._getNextBlockNr(blockname)
            if skip is False:
                for pos in range(match.start, match.start + end):
                    self.chars[pos][1] = blockname
                    self.chars[pos][2] = blocknr

    #            ipshell()

    def matchBlocksDelimiter(self, startpattern, blockname, delimiteropen="{", delimiterclose="}"):
        """
        will look for startpattern, then scan for delimeropen and then start counting, block will stop when asmany closes are found as open delimiters
        ideal find e.g. a code block which is not line based
        will only work on text which is not part of known blocks yet
        @startpattern example to find '{listen,'  startpattern="^[ \t]*{[ \r\n\t]*listen[ \r\n\t]*,"   #note the way how we allow tabs,newlines and spaces
        """
        result = j.data.regex.getRegexMatches(startpattern, self.getText())
        if len(result.matches) == 0:
            pass
        for match in result.matches:
            start = match.start
            nrchars = len(self.chars)
            counter = 0
            state = "start"
            blocknr = self._getNextBlockNr(blockname)
            endpos = 0
            for charpos in range(start, nrchars):
                char = self.chars[charpos][0]
                if char == delimiteropen:
                    if state == "start":
                        startpos = charpos
                    counter += 1
                    state = "scanning"
                if state == "scanning":
                    if self.chars[charpos][1] == "":
                        self.chars[charpos][1] = blockname
                        self.chars[charpos][2] = blocknr
                if char == delimiterclose:
                    counter -= 1
                if counter == 0 and state != "start":
                    endpos = charpos + 1
                    break

    def _getNextBlockNr(self, name):
        if name not in self._higestblocknr:
            self._higestblocknr[name] = 1
        else:
            self._higestblocknr[name] += 1
        return self._higestblocknr[name]

    def getHighestBlockNr(self, name):
        if name not in self._higestblocknr:
            raise j.exceptions.RuntimeError("Cound not find block with name %s" % name)
        else:
            return self._higestblocknr[name]

    def appendBlock(self, startpos, text, blockname=""):
        """
        @param match means block was found and matching
        """
        blocknr = self._getNextBlockNr(blockname)
        for line in text.split("\n"):
            self.lines.append(LTLine(line, blockname, blocknr))

    def deleteBlocks(self, blockname):
        """
        """
        self.chars = [char for char in self.chars if char[1] != blockname]

    def deleteBlock(self, blockname, blocknr=None):
        """
        delete 1 specified block
        @param blocknr
        """
        self.chars = [char for char in self.chars if not (char[1] == blockname and char[2] == blocknr)]

    def delete1Block(self, blockname):
        """
        will check there is only 1 block and that block will be deleted, otherwise raise error
        """
        if self.getHighestBlockNr(blockname) > 1:
            raise j.exceptions.RuntimeError("Found more than 1 block, cannot delete blockname=%s" % blockname)
        self.chars = [char for char in self.chars if char[1] != blockname]

    def getBlock(self, blockname, blocknr):
        """
        get block based on blockname and blocknr
        """
        return string.join([char[0] for char in self.chars if (char[1] == blockname and char[2] == blocknr)], "")

    def get1Block(self, blockname):
        """
        will check there is only 1 block and that block will be returned, otherwise raise error
        """
        if self.getHighestBlockNr(blockname) > 1:
            raise j.exceptions.RuntimeError("Found more than 1 block, cannot get blockname=%s" % blockname)
        return string.join([char[0] for char in self.chars if char[1] == blockname], "")

    def insertBlock(self, start, text, blockname="", blocknr=None):
        """
        block will be inserted at linenr, means line with linenr will be moved backwards
        """
        if blocknr is None and blockname != "":
            blocknr = self._getNextBlockNr(blockname)
        if blocknr is None and blockname == "":
            blocknr = 0
        if blocknr is not None and blockname == "":
            raise j.exceptions.RuntimeError('Cannot have a blockname != "" with blocknr>0')
        if len(text) == 0:
            raise j.exceptions.RuntimeError("Cannot insert empty block of text.")
        counter = start
        textarray = list(text)  # text needs to be reversed otherwise inserting does not go well
        textarray.reverse()
        text = string.join(textarray, "")
        for char in text:
            self.chars.insert(start, [char, blockname, blocknr])
            counter += 1

    def replaceBlock(self, blockname, blocknr, text):
        """
        replace block with new content
        """
        pos = self.getBlockPosition(blockname, blocknr)
        self.deleteBlock(blockname, blocknr)
        self.insertBlock(pos, text, blockname, blocknr)

    #    def replace1Block(self,blockname,text):
    #        """
    #        set block based on startline with new content
    #        """
    #        pos=self.getBlockPosition(blockname)
    #        blocknr=self.chars[pos][2]
    #        self.delete1Block(blockname)
    #        self.insertBlock(pos,text,blockname,blocknr)

    def getBlockPosition(self, blockname, blocknr=None):
        for charnr in range(len(self.chars)):
            # print "%s %s %s" % (charnr,self.chars[charnr][1],self.chars[charnr][2])
            if self.chars[charnr][1] == blockname and (blocknr is None or self.chars[charnr][2] == blocknr):
                return charnr
        raise j.exceptions.RuntimeError("Could not find block with name %s and blocknr %s" % (blockname, blocknr))

    # def __repr__(self):
    # return self.__str__()

    # def __str__(self):
    # return ""

    def printtext(self):
        """
        print line then blocknames then blocknrs
        """
        linepositions = []
        line = ""
        for pos in range(len(self.chars)):
            linepositions.append(pos)
            line += self.chars[pos][0]
            if self.chars[pos][0] == "\n":
                self._log_debug(line)
                # print blocknames
                self._log_debug((string.join(["%s" % self.chars[pos][1] for pos in linepositions])))
                # print blocknrs
                self._log_debug((string.join(["%s" % self.chars[pos][2] for pos in linepositions])))
                line = ""
                linepositions = []
