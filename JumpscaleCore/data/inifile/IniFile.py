from Jumpscale import j

# import Jumpscale as jumpscale

try:
    from configparser import ConfigParser
except BaseException:
    from configparser import ConfigParser

# TODO: UGLY, validation should not happen on object (file) where you read
# from but on file where you populate values (kds)

JSBASE = j.baseclasses.object


class InifileTool(j.baseclasses.object):
    __jslocation__ = "j.data.inifile"

    @staticmethod
    def open(filename, createIfNonExisting=True):
        """Open an existing INI file

        @param filename: Filename of INI file
        @type filename: string

        @raises RuntimeError: When the provided filename doesn't exist

        @returns: Opened INI file object
        @rtype: inifile.IniFile.IniFile
        """
        if isinstance(filename, str) and not j.sal.fs.exists(filename):
            if createIfNonExisting:
                return InifileTool.new(filename)
            else:
                raise j.exceptions.RuntimeError("Attempt to open non-existing INI file %s" % filename)
        return IniFile(filename, create=False)

    @staticmethod
    def new(filename):
        """Create a new INI file

        @param filename: Filename of INI file
        @type filename: string

        @raises RuntimeError: When the provided filename exists

        @returns: New INI file object
        @rtype: inifile.IniFile.IniFile
        """
        if isinstance(filename, str) and j.sal.fs.exists(filename):
            raise j.exceptions.RuntimeError("Attempt to create existing INI file %s as a new file" % filename)
        return IniFile(filename, create=True)


class IniFile(j.baseclasses.object):
    """
    Use with care:
    - addParam and setParam are 'auto-write'
    - addSection isn't
    - removeSection isn't
    - removeParam isn't
    """

    __configParser = None  # ConfigParser
    __inifilepath = None  # string
    __file = None  # File-like object
    __removeWhenDereferenced = False  # bool

    def __init__(self, iniFile, create=False, removeWhenDereferenced=False):
        """ Initialize IniFile. If the file already exists, read it and parse the structure.
            If the file did not yet exist. Don't do anything yet.

            @param iniFile:                The file to write to. This can be either a string representing a file-path or a file-like object
            @type iniFile:                 string or file-like object
            @param create:                 Whether or not to create a new file (Ignored if iniFile is a file-like object)
            @type create: bool
            @param removeWhenDereferenced: Whether or not to remove the file when this object is dereferenced
            @type removeWhenDereferenced:  bool
        """
        JSBASE.__init__(self)
        self.__configParser = ConfigParser()
        self.__removeWhenDereferenced = removeWhenDereferenced
        if isinstance(iniFile, str):  # iniFile is a filepath
            self.__inifilepath = iniFile
            if create:
                j.sal.fs.createDir(j.sal.fs.getDirName(iniFile))
                self._log_info("Create config file: " + iniFile)
                j.sal.fs.writeFile(iniFile, "")
            if not j.sal.fs.isFile(iniFile):
                raise j.exceptions.RuntimeError("Inifile could not be found on location %s" % iniFile)
        else:  # iniFile is a file-like object
            self.__file = iniFile

        self.__readFile()

    def __str__(self):
        """Returns string representation of the IniFile"""
        return "<IniFile> filepath: %s " % self.__inifilepath

    __repr__ = __str__

    def __del__(self):
        if self.__inifilepath and self.__removeWhenDereferenced:
            j.sal.fs.remove(self.__inifilepath)

    def __readFile(self):
        # content=j.sal.fs.readFile(self.__inifilepath)
        fp = None
        try:
            if self.__inifilepath:
                fp = open(self.__inifilepath, "r")
            else:
                fp = self.__file
            return self.__configParser.readfp(fp)
        except Exception as err:
            self._log_error(err)
            if fp and not fp.closed:
                fp.close()
            raise j.exceptions.RuntimeError("Failed to read the inifile \nERROR: %s" % (str(err)))

    def getSections(self):
        """ Return list of sections from this IniFile"""
        try:
            return self.__configParser.sections()
        except Exception as err:
            raise j.exceptions.NotFound("Failed to get sections \nERROR: %s" % str(err))

    def getParams(self, sectionName):
        """ Return list of params in a certain section of this IniFile
        @param sectionName: Name of the section for which you wish the param"""
        if not self.checkSection(sectionName):
            return
        try:
            return self.__configParser.options(sectionName)
        except Exception as err:
            raise j.exceptions.NotFound(
                "Failed to get parameters under the specified section: %s \nERROR: %s" % (sectionName, str(err))
            )

    def checkSection(self, sectionName):
        """ Boolean indicating whether section exists in this IniFile
        @param sectionName: name of the section"""
        try:
            return self.__configParser.has_section(sectionName)
        except Exception as err:
            raise j.exceptions.Value(
                "Failed to check if the specified section: %s exists \nERROR: %s" % (sectionName, str(err))
            )

    def checkParam(self, sectionName, paramName):
        """Boolean indicating whether parameter exists under this section in the IniFile
        @param sectionName: name of the section where the param should be located
        @param paramName:   name of the parameter you wish to check"""
        try:
            return self.__configParser.has_option(sectionName, paramName)
        except Exception as e:
            raise j.exceptions.Value(
                "Failed to check if the parameter: %s under section: %s exists \nERROR: %s"
                % (paramName, sectionName, str(e))
            )

    def getValue(self, sectionName, paramName, raw=False, default=None):
        """ Get value of the parameter from this IniFile
        @param sectionName: name of the section
        @param paramName:   name of the parameter
        @param raw:         boolean specifying whether you wish the value to be returned raw
        @param default: if given and the value does not exist the default value will be given
        @return: The value"""
        if default is not None and not self.checkParam(sectionName, paramName):
            return default
        try:
            result = self.__configParser.get(sectionName, paramName, raw=raw)
            self._log_info(
                "Inifile: get %s:%s from %s, result:%s" % (sectionName, paramName, self.__inifilepath, result)
            )
            return result
        except Exception as err:
            raise j.exceptions.NotFound(
                "Failed to get value of the parameter: %s under section: %s in file %s.\nERROR: %s"
                % (paramName, sectionName, self.__inifilepath, str(err))
            )

    def getBooleanValue(self, sectionName, paramName):
        """Get boolean value of the specified parameter
        @param sectionName: name of the section
        @param paramName:   name of the parameter"""
        try:
            result = self.__configParser.getboolean(sectionName, paramName)
            self._log_info(
                "Inifile: get boolean %s:%s from %s, result:%s" % (sectionName, paramName, self.__inifilepath, result)
            )
            return result

        except Exception as e:
            raise j.exceptions.NotFound(
                "Inifile: Failed to get boolean value of parameter:%s under section:%s \nERROR: %s"
                % (paramName, sectionName, e)
            )

    def getIntValue(self, sectionName, paramName):
        """Get an integer value of the specified parameter
        @param sectionName: name of the section
        @param paramName:   name of the parameter"""
        try:
            result = self.__configParser.getint(sectionName, paramName)
            self._log_info(
                "Inifile: get integer %s:%s from %s, result:%s" % (sectionName, paramName, self.__inifilepath, result)
            )
            return result
        except Exception as e:
            raise j.exceptions.NotFound(
                "Failed to get integer value of parameter: %s under section: %s\nERROR: %s"
                % (paramName, sectionName, e)
            )

    def getFloatValue(self, sectionName, paramName):
        """Get float value of the specified parameter
        @param sectionName: name of the section
        @param paramName:   name of the parameter"""
        try:
            result = self.__configParser.getfloat(sectionName, paramName)
            self._log_info(
                "Inifile: get integer %s:%s from %s, result:%s" % (sectionName, paramName, self.__inifilepath, result)
            )
            return result
        except Exception as e:
            raise j.exceptions.NotFound(
                "Failed to get float value of parameter:%s under section:%s \nERROR: %" % (paramName, sectionName, e)
            )

    def addSection(self, sectionName):
        """ Add a new section to this Inifile. If it already existed, silently pass
        @param sectionName: name of the section"""
        try:
            if self.checkSection(sectionName):
                return
            self._log_info("Inifile: add section %s to %s" % (sectionName, self.__inifilepath))
            self.__configParser.add_section(sectionName)
            if self.checkSection(sectionName):
                return True
        except Exception as err:
            raise j.exceptions.RuntimeError(
                "Failed to add section with sectionName: %s \nERROR: %s" % (sectionName, str(err))
            )

    def addParam(self, sectionName, paramName, newvalue):
        """ Add name-value pair to section of IniFile
        @param sectionName: name of the section
        @param paramName:   name of the parameter
        @param newValue:    value you wish to assign to the parameter"""
        try:
            if str(newvalue) == "none":
                newvalue == "*NONE*"
            self.__configParser.set(sectionName, paramName, str(newvalue))
            self._log_info("Inifile: set %s:%s=%s on %s" % (sectionName, paramName, str(newvalue), self.__inifilepath))
            # if self.checkParam(sectionName, paramName):
            #    return True
            self.write()
            return False
        except Exception as err:
            raise j.exceptions.RuntimeError(
                "Failed to add parameter with sectionName: %s, parameterName: %s, value: %s \nERROR: %s"
                % (sectionName, paramName, newvalue, str(err))
            )

    def setParam(self, sectionName, paramName, newvalue):
        """ Add name-value pair to section of IniFile
        @param sectionName: name of the section
        @param paramName:   name of the parameter
        @param newValue:    value you wish to assign to the parameter"""
        self.addParam(sectionName, paramName, newvalue)

    def removeSection(self, sectionName):
        """ Remove a section from this IniFile
        @param sectionName: name of the section"""
        if not self.checkSection(sectionName):
            return False
        try:
            self.__configParser.remove_section(sectionName)
            self._log_info("inifile: remove section %s on %s" % (sectionName, self.__inifilepath))
            if self.checkSection(sectionName):
                return False
            return True
        except Exception as err:
            raise j.exceptions.RuntimeError("Failed to remove section %s with \nERROR: %s" % (sectionName, str(err)))

    def removeParam(self, sectionName, paramName):
        """ Remove a param from this IniFile
        @param sectionName: name of the section
        @param paramName:   name of the parameter"""
        if not self.checkParam(sectionName, paramName):
            return False
        try:
            self.__configParser.remove_option(sectionName, paramName)
            self._log_info("Inifile:remove %s:%s from %s" % (sectionName, paramName, self.__inifilepath))
            return True
        except Exception as err:
            raise j.exceptions.RuntimeError(
                "Failed to remove parameter: %s under section: %s \nERROR: %s" % (paramName, sectionName, str(err))
            )

    def write(self, filePath=None):
        """ Write the IniFile content to disk
        This completely overwrites the file
        @param filePath: location where the file will be written
        """
        closeFileHandler = True
        fp = None
        self._log_info("Inifile: Write configfile %s to disk" % (self.__inifilepath))
        if not filePath:
            if self.__inifilepath:  # Use the inifilepath that was set in the constructor
                filePath = self.__inifilepath
            elif self.__file:  # write to the file-like object that was set in the constructor
                closeFileHandler = False  # We don't want to close this object
                fp = self.__file
                fp.seek(0)
                fp.truncate()  # Clear the file-like object before writing to it
            else:  # Nothing to write to
                raise Exception("No filepath to write to")

        try:
            if not fp:
                j.tools.lock.lock(filePath)
                fp = open(filePath, "w")  # Completely overwrite the file.
            self.__configParser.write(fp)
            fp.flush()
            if closeFileHandler:
                fp.close()
                j.tools.lock.unlock(filePath)

        except Exception as err:
            if fp and closeFileHandler and not fp.closed:
                fp.close()
                j.sal.fs.unlock_(filePath)
            raise j.exceptions.RuntimeError("Failed to update the inifile at '%s'\nERROR: %s\n" % (filePath, str(err)))

    def getContent(self):
        """ Get the Inifile content to a string
        """
        # TODO: jumpscale primitives should be used (no fp...)
        fp = None
        if self.__file and not self.__file.closed:
            fp = self.__file
            fp.seek(0)
            fp.truncate()
        else:
            try:
                from io import StringIO
            except ImportError:
                from io import StringIO
            fp = StringIO()
        self.__configParser.write(fp)
        fp.seek(0)
        return fp.read()

    def getSectionAsDict(self, section):
        retval = {}
        for key in self.getParams(section):
            retval[key] = self.getValue(section, key)
        return retval

    def getFileAsDict(self):
        retval = {}
        for section in self.getSections():
            retval[section] = self.getSectionAsDict(section)
        return retval
