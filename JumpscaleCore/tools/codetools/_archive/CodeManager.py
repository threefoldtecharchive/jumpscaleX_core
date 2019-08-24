from Jumpscale import j
import re

# @review [kristof,incubaid] name:codereviewtools tools for codereview, check all new code
JSBASE = j.baseclasses.object


class CodeManager(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)
        self.ignoreDirs = ["/.hg*"]
        self.users = {}
        self.groups = {}

    def setusers(self, config):
        for line in config.split("\n"):
            line = line.strip()
            if line != "":
                if line[0] != "#":
                    if line.find("#") != -1:
                        line = line.split("#")[0]
                    if line.find(":") != -1:
                        userid, aliases = line.split(":")
                        self.users[userid] = userid
                        aliases = aliases.split(",")
                        for alias in aliases:
                            self.users[alias.lower()] = userid.lower()

    def setgroups(self, config):
        for line in config.split("\n"):
            line = line.strip()
            if line != "":
                if line[0] != "#":
                    if line.find("#") != -1:
                        line = line.split("#")[0]
                    if line.find(":") != -1:
                        groupid, grouptext = line.split(":")
                        groups = grouptext.split(",")
                        groups = [group.lower() for group in groups]
                        self.groups[groupid.lower()] = groups
        # resolve groups in groups
        for i in range(5):
            for groupid in list(self.groups.keys()):
                result = []
                for item in self.groups[groupid]:
                    if item in self.groups:
                        result.extend(self.groups[item])
                    else:
                        result.append(item)
                self.groups[groupid] = result

    def getUserId(self, username):
        if username in self.users:
            return self.users[username]
        else:
            return False

    def _pathIgnoreCheck(self, path):
        for item in self.ignoreDirs:
            item = item.replace(".", "\\.")
            item = item.replace("*", ".*")
            if j.data.regex.match(item, path):
                return True
        return False

    def getCodeManagerForFile(self, path):
        return CodeManagerFile(self, path)

    def parse(self, path):
        """
        directory to walk over and find story, task, ... statements
        """
        self.rootpath = path
        files = []
        # TODO: P1 this is not very nice, should be done in one go, also make sure we don't descend in .hg dirs
        files.extend(j.sal.fs.listFilesInDir(path, True, filter="*.py"))
        files.extend(j.sal.fs.listFilesInDir(path, True, filter="*.txt"))
        files.extend(j.sal.fs.listFilesInDir(path, True, filter="*.md"))
        files.extend(j.sal.fs.listFilesInDir(path, True, filter="*.wiki"))
        for pathItem in files:
            if not self._pathIgnoreCheck(pathItem):
                path2 = pathItem.replace(path, "")
                self._log_debug(("parse %s" % path2))
                if (
                    not path2
                    == "/apps/incubaiddevelopmentprocess/appserver/service_developmentprocess/extensions/codeparser/Parser.py"
                ):
                    if path2[0] == "/":
                        path3 = path2[1:]
                    codemanagerfile = CodeManagerFile(self, path3)
                    codemanagerfile.process()


class CodeManagerFile(j.baseclasses.object):
    """
    manages code for one file
    """

    def __init__(self, codemanager, path):
        JSBASE.__init__(self)
        self.users = j.tools.code.codemanager.users
        self.groups = j.tools.code.codemanager.groups
        self.path = path
        self.code = j.sal.fs.readFile(path)
        self.nrlines = len(self.code)
        self.codemanager = codemanager

    def process(self):
        if self.code.strip() != "":
            self._findUsers(code, path3, pathItem)
            self._findStories(code, path3, pathItem)
            self._findScrumteams(code, path3, pathItem)
            self._findSprints(code, path3, pathItem)
            self._findTasks(code, path3, pathItem)
            self._findRoadmapitems(code, path3, pathItem)
            self._findGroups(code, path3, pathItem)

    def findItems(self, item="@owner", maxitems=0):
        result = []
        if maxitems == 0:
            maxitems = 10000000000

        def process(arg, line):
            line = line.split(item)[1].strip()
            if line.find("(") != -1:
                line = line.split("(")[0].strip()
            result.append(line)
            return ""

        text2 = j.data.regex.replaceLines(process, arg="", text=self.code, includes=["%s.*" % item], excludes="")
        if len(result) > maxitems:
            self.errorTrap("Error in text to parse, found more entities:%s than %s" % (item, maxitems))
        if maxitems == 1:
            if len(result) > 0:
                result = result[0]
            else:
                result = ""
        return result

    def findLine(self, text, item="@owner"):
        for line in text.split("\n"):
            if line.strip().lower().find(item) == 0:
                return line
        return ""

    def findId(self, text, path):
        result = j.data.regex.findAll("\(\(.*: *\d* *\)\)", text)

        if len(result) > 1:
            raise j.exceptions.RuntimeError("Found 2 id's in %s" % path)
        if len(result) == 1:
            result = result[0].split(":")[1]
            result = result.split(")")[0]
        else:
            result = ""
        if result.strip() == "":
            result = 0
        else:
            try:
                result = int(result)
            except Exception as e:
                raise j.exceptions.RuntimeError("Could not parse if, error:%s. \nPath = %s" % (e, path))

        return text, result

    def parseTimeInfo(self, timestring, modelobj, defaults=[8, 16, 8, 4, 8]):
        # self._log_debug "timestring: %s" % timestring
        timeItems = timestring.split("/")
        modelobj.time_architecture = defaults[0]
        modelobj.time_coding = defaults[1]
        modelobj.time_integration = defaults[2]
        modelobj.time_doc = defaults[3]
        modelobj.time_testing = defaults[4]
        modelobj.timestr = timestring
        modelobj.time = 0
        for item in timeItems:
            if item != "":
                if item.lower()[0] == "a":
                    modelobj.time_architecture = int(item.lower().replace("a", ""))
                    modelobj.time += modelobj.time_architecture
                if item.lower()[0] == "c":
                    modelobj.time_coding = int(item.lower().replace("c", ""))
                    modelobj.time += modelobj.time_coding
                if item.lower()[0] == "i":
                    modelobj.time_integration = int(item.lower().replace("i", ""))
                    modelobj.time += modelobj.time_integration
                if item.lower()[0] == "d":
                    modelobj.time_doc = int(item.lower().replace("d", ""))
                    modelobj.time += modelobj.time_doc
                if item.lower()[0] == "t":
                    modelobj.time_testing = int(item.lower().replace("t", ""))
                    modelobj.time += modelobj.time_testing

    def _parseTaskInfo(self, storyTaskModelObject, info):
        for item in info.split(" "):
            if item != "":
                if item.lower()[0] == "s":
                    # story
                    storyTaskModelObject.storyid = int(item.lower().replace("s", ""))
                elif item.lower()[0] == "p":
                    # priority
                    storyTaskModelObject.priority = int(item.lower().replace("p", ""))
                elif item.lower()[0] == "m":
                    # sprint
                    storyTaskModelObject.sprintid = int(item.lower().replace("m", ""))

    def _parseStoryInfo(self, storyTaskModelObject, info):
        for item in info.split(" "):
            if item != "":
                if item.lower()[0] == "s":
                    # story
                    storyTaskModelObject.id = int(item.lower().replace("s", ""))
                elif item.lower()[0] == "p":
                    # priority
                    storyTaskModelObject.priority = int(item.lower().replace("p", ""))
                elif item.lower()[0] == "m":
                    # sprint
                    storyTaskModelObject.sprintid = int(item.lower().replace("m", ""))

    def getUsers(self, text):
        """
        return [$text,$users] with unique id and the usergroup construct is taken out of text, all groups are resolved to users
        """
        # items=j.data.regex.findAll("[a-z]*:[a-z]*","s: d:d")
        items = j.data.regex.findAll("\[[a-z, ]*\]", text)
        text = text.lower()
        if len(items) > 1:
            raise j.exceptions.RuntimeError(
                "Found to many users,groups items in string, needs to be one [ and one ] and users & groups inside, now %s"
                % text
            )
        if len(items) == 0:
            return text, []
        usergroups = items[0]
        text = text.replace(usergroups, "").replace("  ", " ").strip()
        items = usergroups.replace("[", "").replace("]", "").split(",")
        users = []

        for item in items:
            item = item.strip()
            if item in self.groups:
                for user in self.groups[item]:
                    users.append(user)
            if item in self.users:
                users.append(item)
            # get aliases
            usersout = []
            for user in users:
                if user in self.users:
                    if self.users[user] not in usersout:
                        usersout.append(self.users[user])
        return text, usersout

    def parseBasics(self, text):
        """
        @return  [infoitems,timeitem,users,tags,descr]
        """
        keys = ["P", "p", "S", "s", "M", "m"]
        timeitem = ""
        infoitems = ""
        descr = ""
        state = "start"
        tags = ""
        # self._log_debug "parse task: %s" % text
        text, users = self.getUsers(text)
        text = text.replace("  ", " ")
        text = text.replace("  ", " ")
        if text.strip() == "":
            return ["", "", "", "", ""]
        usersfound = False
        for item in text.strip().split(" "):
            # self._log_debug "item:  %s" % item
            if state == "endofmeta":
                descr += item + " "
            if state == "start":
                if item[0] in keys:
                    try:
                        int(item[1:])
                        infoitems += item + " "
                    except BaseException:
                        descr += item + " "
                        state = "endofmeta"
                elif item[0:2].lower() == "t:":
                    timeitem = item[2:]
                    if not re.match(r"[aAcCiIdDtT/\d:]*\Z", timeitem):
                        descr += item + " "
                        state = "endofmeta"
                        timeitem = ""
                        # raise j.exceptions.RuntimeError("Time item match failed for text %s" % text)
                elif item.find(":") != -1:
                    tags += "%s " % item
                else:
                    descr += item + " "
                    state = "endofmeta"
        return [infoitems, timeitem, users, tags, descr]

    def _getStoryName(self, info):
        out = ""
        for item in info.split(" "):
            if not (item.lower()[0] == "s" or item.lower()[0] == "p" or item.lower()[0] == "m"):
                out += " %s" % item
        return out.strip()

    def _findStories(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@storydef") != -1:
                # found a story
                lineFull = self.findLine(item, "@story")
                id1 = self.addUniqueId(lineFull, fullPath, ttype="story")
                text2 = item
                text2, owners = self.findItem(text2, "@owner")
                text2, priority = self.findItem(text2, "@priority")
                if priority == "":
                    priority = 2
                text2, roadmap = self.findItem(text2, "@roadmap")
                text2, sprint = self.findItem(text2, "@sprint")
                text2, storydependencies = self.findItem(text2, "@storydependencies")
                text2, roadmapdependencies = self.findItem(text2, "@roadmapdependencies")
                text2, time = self.findItem(text2, "@time")
                story, storyinfo2 = self.findItem(text2, "@story")
                storyinfo, timetextdonotuse, userdonotuse, groupdonotuse, descr = self.parseTaskQuestionRemark(
                    storyinfo2
                )
                if len(descr) < 5:
                    raise j.exceptions.RuntimeError("Story description is less than 5 for path %s" % fullPath)

                storyname = descr

                obj = self.projectInfoObject.stories.addStory(id=id1, name=storyname.strip(), description=story.strip())
                obj.model.owner = owners
                self._parseStoryInfo(obj.model, storyinfo)
                self.parseTimeInfo(time, obj.model)
                obj.model.path = fullPath
                obj.model.storydependencies = self._strToArrayInt(storydependencies)
                obj.model.roadmapdependencies = self._strToArrayInt(roadmapdependencies)
                obj.model.sprintid = self._strToInt(sprint)
                obj.model.priority = self._strToInt(priority)
                obj.model.roadmapid = self._strToInt(roadmap)

    def _findScrumteams(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@scrumteamdef") != -1:
                # found a story
                lineFull = self.findLine(item, "@scrumteamdef")
                id1 = self.addUniqueId(lineFull, fullPath, ttype="scrumteam")
                text2 = item
                text2, owners = self.findItem(text2, "@owner")
                descr, name = self.findItem(text2, "@scrumteamdef")
                if len(descr) < 5:
                    raise j.exceptions.RuntimeError("Scrumteam description is less than 5 for path %s" % fullPath)
                obj = self.projectInfoObject.scrumteams.addScrumteam(
                    id=id1, name=name.strip(), description=descr.strip()
                )
                obj.model.owner = owners
                obj.model.path = fullPath
                obj.model.id = id1

    def _findSprints(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@sprintdef") != -1:
                # found a story
                lineFull = self.findLine(item, "@sprintdef")
                id1 = self.addUniqueId(lineFull, fullPath, ttype="sprint")
                text2 = item
                text2, owners = self.findItem(text2, "@owner")
                text2, scrumteam = self.findItem(text2, "@scrumteam")
                text2, company = self.findItem(text2, "@company")
                text2, deadline = self.findItem(text2, "@deadline")
                text2, start = self.findItem(text2, "@start")
                text2, goal = self.findItem(text2, "@goal")
                descr, line = self.findItem(text2, "@sprintdef")
                sprintinfo, timetextdonotuse, userdonotuse, groupdonotuse, name = self.parseTaskQuestionRemark(line)
                sprintinfo = sprintinfo.strip()
                obj = self.projectInfoObject.sprints.addSprint(id=id1, name=name.strip(), description=descr.strip())
                obj.model.ownername = owners
                obj.model.path = fullPath
                obj.model.goal = goal
                obj.model.id = id1
                obj.model.company = company
                obj.model.deadline = int(j.data.time.HRDatetoEpoch(deadline.replace("-", "/")))
                obj.model.start = int(j.data.time.HRDatetoEpoch(start.replace("-", "/")))

    def _strToArrayInt(self, items):
        if items == "":
            return []
        result = ""
        for item in items.split(","):
            try:
                result.append(int(item))
            except BaseException:
                raise j.exceptions.RuntimeError("Cannot convert str to array, item was %s" % item)
        return result

    def _strToInt(self, item):
        if item == "":
            return 0
        try:
            result = int(item)
        except BaseException:
            raise j.exceptions.RuntimeError("Cannot convert str to int, item was %s" % item)
        return result

    def _findRoadmapitems(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@roadmapdef") != -1:
                # found a story
                lineFull = self.findLine(item, "@roadmapdef")
                text2 = item
                text2, owners = self.findItem(text2, "@owner")
                text2, priority = self.findItem(text2, "@priority")
                if priority == "":
                    priority = 2
                text2, goal = self.findItem(text2, "@goal")
                text2, releasedate_int = self.findItem(text2, "@releasedate_int")
                text2, releasedate_pub = self.findItem(text2, "@releasedate_pub")
                text2, bugs = self.findItem(text2, "@bugs")
                text2, company = self.findItem(text2, "@company")
                text2, product = self.findItem(text2, "@product")
                text2, storydependencies = self.findItem(text2, "@storydependencies")
                text2, roadmapdependencies = self.findItem(text2, "@roadmapdependencies")
                text2, featurerequests = self.findItem(text2, "@featurerequests")
                descr, line = self.findItem(text2, "@roadmapdef")
                descr, remarks = self._descrToDescrAndRemarks(descr)
                sprintinfodonotuse, timetextdonotuse, userdonotuse, groupdonotuse, name = self.parseTaskQuestionRemark(
                    line
                )
                if len(descr) < 5:
                    raise j.exceptions.RuntimeError("Roadmap description is less than 5 for path %s" % fullPath)
                id1 = self.addUniqueId(lineFull, fullPath, ttype="roadmapitem")
                obj = self.projectInfoObject.roadmapitems.addRoadmapitem(
                    id=id1, name=name.strip(), description=descr.strip()
                )
                obj.model.id = id1
                obj.model.owner = owners
                obj.model.path = fullPath
                obj.model.goal = goal
                obj.model.priority = int(priority)
                obj.model.remarks = remarks
                obj.model.releasedate_int = int(j.data.time.HRDatetoEpoch(releasedate_int.replace("-", "/")))
                obj.model.releasedate_pub = int(j.data.time.HRDatetoEpoch(releasedate_pub.replace("-", "/")))
                obj.model.featurerequests = self._strToArrayInt(featurerequests)
                obj.model.bugs = self._strToArrayInt(bugs)
                obj.model.company = company
                obj.model.product = product
                obj.model.storydependencies = self._strToArrayInt(storydependencies)
                obj.model.roadmapdependencies = self._strToArrayInt(roadmapdependencies)
                # obj.model.sprintids=self._strToArrayInt(sprintids)

    def _findUsers(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@userdef") != -1:
                lineFull = self.findLine(item, "@userdef")
                id1 = self.addUniqueId(lineFull, fullPath, ttype="user")
                text2 = item
                text2, phone = self.findItem(text2, "@phone")
                text2, email = self.findItem(text2, "@email")
                text2, aliases = self.findItem(text2, "@aliases")
                descr, firstline = self.findItem(text2, "@userdef")
                sprintinfodonotuse, timetextdonotuse, userdonotuse, groupdonotuse, name = self.parseTaskQuestionRemark(
                    firstline
                )
                obj = self.projectInfoObject.users.addUser(id=id1, name=name.strip(), description=descr.strip())
                obj.model.path = fullPath
                obj.model.aliases = [item.lower().strip() for item in aliases.split(",")]
                obj.model.phone = phone
                obj.model.email = email

    def _findGroups(self, text, path, fullPath):
        found = j.data.regex.extractBlocks(text, includeMatchingLine=False, blockStartPatterns=['"""'])
        for item in found:
            if item.lower().find("@groupdef") != -1:
                lineFull = self.findLine(item, "@groupdef")
                id1 = self.addUniqueId(lineFull, fullPath, ttype="group")
                text2 = item
                text2, email = self.findItem(text2, "@email")
                text2, aliases = self.findItem(text2, "@aliases")
                descr, firstline = self.findItem(text2, "@groupdef")
                sprintinfodonotuse, timetextdonotuse, userdonotuse, groupdonotuse, name = self.parseTaskQuestionRemark(
                    firstline
                )
                obj = self.projectInfoObject.groups.addGroup(id=id1, name=name.strip(), descr=descr.strip())
                obj.model.path = fullPath
                obj.model.aliases = aliases.split(",")
                obj.model.email = email

    def _descrToDescrAndRemarks(self, text):
        if text.find("=======") != -1:
            out = ""
            descr = ""
            intdescr = ""
            lines = sprint.model.description.split("\n")
            state = start
            for line in lines:
                if line.find("======") == -1 and state == "start":
                    descr += line + "\n"
                if state == "int":
                    intdescr += line + "\n"
                if line.find("======") != -1:
                    state = "int"
            return descr, intdescr
        else:
            return text, ""

    def _normalizeDescr(self, text):
        text = text.lower()
        splitat = ["{", "(", "[", "#", "%", "$", "'"]
        for tosplit in splitat:
            if len(text.split(tosplit)) > 0:
                text = text.split(tosplit)[0]
        text = text.replace(",", "")
        text = text.replace(":", "")
        text = text.replace(";", "")
        text = text.replace("  ", " ")
        if text != "" and text[-1] == " ":
            text = text[:-1]
        text = text.replace("-", "")
        text = text.replace("_", "")
        return text

    def shortenDescr(self, text, maxnrchars=60):
        return j.tools.code.textToTitle(text, maxnrchars)

    def _getLinesAround(self, path, tofind, nrabove, nrbelow):
        text = j.sal.fs.readFile(path)
        nr = 0
        lines = text.split("\n")
        for line in lines:
            if line.find(tofind) != -1:
                if nr - nrabove < 0:
                    nrstart = 0
                else:
                    nrstart = nr - nrabove
                if nr + nrabove > len(lines):
                    nrstop = len(lines)
                else:
                    nrstop = nr + nrabove
                return "\n".join(lines[nrstart:nrstop])
            nr += 1
        return ""

    def addUniqueId(self, line, fullPath, ttype="sprint"):
        line, id1 = self.findId(line, fullPath)
        if id1 == 0:
            # create unique id and put it in the file
            id1 = j.data.idgenerator.generateIncrID("%sid" % ttype, self.service)
            # tfe=j.tools.code.getTextFileEditor(fullPath)
            # tfe.addItemToFoundLineOnlyOnce(line," ((%s:%s))"%(ttype,id1),"\(id *: *\d* *\)",reset=True)
            tfe = j.tools.code.getTextFileEditor(fullPath)
            tfe.addItemToFoundLineOnlyOnce(line, " ((%s:%s))" % (ttype, id1), "\(+.*: *\d* *\)+", reset=self.reset)
        return id1

    def _findTasks(self, text, path, fullPath):
        # TODO: S2 do same for remarks & questions
        def findTodoVariants(line):
            variants = ["@todo:", "TODO: :", "@todo"]
            for variant in variants:
                if line.strip().find(variant) == 0:
                    return variant

        if text.lower().find("@todo") != -1:
            lines = j.data.regex.findAll("@todo.*", text)
            for line in lines:
                self.addUniqueId(line, fullPath, ttype="todo")
                line, id1 = self.findId(line, fullPath)
                todostatement = findTodoVariants(line)
                line1 = line.replace(todostatement, "")
                infotext, timetext, user, group, descr = self.parseTaskQuestionRemark(line1)

                obj = self.projectInfoObject.tasks.addTask(id=id1, descr=descr.strip())
                obj.model.storyid = 0
                obj.model.users = user
                obj.model.group = group
                obj.model.path = fullPath
                obj.model.context = self._getLinesAround(fullPath, line, 10, 20)

                obj.model.descrshort = self.shortenDescr(descr)
                self._log_debug(("tasktext:%s" % line))
                # self._log_debug "infotext:%s" % infotext
                self._parseTaskInfo(obj.model, infotext)
                self.parseTimeInfo(timetext, obj.model, defaults=[0, 1, 0, 1, 0])
                if obj.model.storyid == 0:
                    obj.model.storyid = 999  # 999 is the unsorted story card

    def findLineNr(self, text):
        linenr = 0
        for line in self.code.split("\n"):
            linenr += 1
            if line.find(text) != -1:
                return linenr
        else:
            return False

    def findReviews(self):
        """
        return [[name,description,users,linefrom,lineto]]
        """
        items = self.findItems("@review")
        result = []
        for item in items:
            linenr = self.findLineNr(item)
            [infoitems, timeitem, users, tags, descr] = self.parseBasics(item)
            tags = tags.lower()
            tt = j.data.tags.getObject(tags)
            if tt.tagExists("line"):
                linesfromto = tt.tagGet("line")
                items = linesfromto.split(",")
                for item in items:
                    if item.strip()[0] == "-":
                        linefrom = linenr - int(item[1:].strip())
                        if linefrom < 1:
                            linefrom = 1
                    if item.strip()[0] == "+":
                        lineto = linenr + int(item[1:].strip())
            else:
                linefrom = 1
                lineto = self.nrlines
            if tt.tagExists("name"):
                name = tt.tagGet("name")
            else:
                name = ""
            result.append([name, descr, users, linefrom, lineto, linenr])
        return result

    def errorTrap(self, msg):
        j.tools.console.echo("ERROR: %s" % msg)

    def __str__(self):
        ss = ""
        ss += "%s\n" % self.model.sprints
        ss += "%s\n" % self.model.stories
        ss += "%s\n" % self.model.tasks
        ss += "%s\n" % self.model.users
        ss += "%s\n" % self.model.groups
        ss += "%s\n" % self.model.remarks
        ss += "%s\n" % self.model.questions
        return ss

    def __repr__(self):
        return self.__str__()
