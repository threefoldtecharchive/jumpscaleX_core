# builder library for tools

use as 

```
self.tools.... 
````

## methods

```python3

class tools():
    
    def cd(self, path):
        """cd to the given path"""

    def pwd(self):
        """        
        :return current path 
        """
    
    def command_check(self, command):
        """Tests if the given command is available on the system."""    

    def command_location(self, command):
        """return location of cmd"""

    def dir_copy(self, source, dest, keepsymlinks=False, deletefirst=False,
                 overwriteFiles=True, ignoredir=[".egg-info", ".dist-info"], ignorefiles=[".egg-info"],
                 recursive=True, rsyncdelete=False, createdir=False):
        """
        std excludes are done like "__pycache__" no matter what you specify
        Recursively copy an entire directory tree rooted at src.
        The dest directory may already exist; if not,
        it will be created as well as missing parent directories
        @param source: string (source of directory tree to be copied)
        @param dest: string (path directory to be copied to...should not already exist)
        @param keepsymlinks: bool (True keeps symlinks instead of copying the content of the file)
        @param deletefirst: bool (Set to True if you want to erase destination first, be carefull, this can erase directories)
        @param overwriteFiles: if True will overwrite files, otherwise will not overwrite when destination exists
        """

    def dir_attribs(self, location, mode=None, owner=None, group=None, recursive=False, showout=False):
        """Updates the mode / owner / group for the given remote directory."""

    def dir_ensure(self, location, recursive=True, mode=None, owner=None, group=None):
        """Ensures that there is a remote directory at the given location,
        optionally updating its mode / owner / group.

        If we are not updating the owner / group then this can be done as a single
        ssh call, so use that method, otherwise set owner / group after creation."""                    

    def dir_exists(self, location):

    def dir_remove(self, location, recursive=True):

    def exists(self, location, replace=True):

    def file_attribs(self, location, mode=None, owner=None, group=None):
        """
        Updates the mode/owner/group for the remote file at the given
        location.

        :param mode: mode of file, sent as Octal, defaults to None
        :type mode: Octal, optional
        :param owner: owner of file, defaults to None
        :type owner: string, optional
        :param group: owning group, defaults to None
        :type group: string, optional
        """

    def file_attribs_get(self, location):
        """Return mode, owner, and group for remote path.
        Return mode, owner, and group if remote path exists, 'None'
        otherwise.
        """

    def file_backup(self, location, suffix=".orig", once=False):
        """Backups the file at the given location in the same directory, appending
        the given suffix. If `once` is True, then the backup will be skipped if
        there is already a backup file."""

    def file_base64(self, location):

    def file_copy(self, source, dest, recursive=False, overwrite=True):

    def file_download(
            self,url,to="",overwrite=True,retry=3,timeout=0,login="",passwd="",minspeed=0,
            multithread=False,expand=False,minsizekb=40,removeTopDir=False,deletedest=False):
        """
        download from url
        @return path of downloaded file
        @param to is destination
        @param minspeed is kbytes per sec e.g. 50, if less than 50 kbytes during 10 min it will restart the download (curl only)
        @param when multithread True then will use aria2 download tool to get multiple threads
        @param removeTopDir : if True and there is only 1 dir in the destination then will move files away from the one dir to parent (often in tgz the top dir is not relevant)
        """

    def file_ensure(self, location, mode=None, owner=None, group=None):
        """Updates the mode/owner/group for the remote file at the givenlocation."""                                            

    def file_exists(self, location):

    def file_expand(self, path, destination="", removeTopDir=False):

    def file_get_tmp_path(self, basepath=""):

    def file_is_dir(self, location):                    
    def file_is_file(self, location):
    def file_is_link(self, location):

    def file_link(self, source, destination, symbolic=True, mode=None, owner=None, group=None):
        """Creates a (symbolic) link between source and destination on the remote host,
        optionally setting its mode / owner / group."""

    def file_md5(self, location):

    def file_move(self, source, dest, recursive=False):
    def file_read(self, location, default=None):

    def file_remove_prefix(self, location, prefix, strip=True):

    def file_sha256(self, location):
    def file_size(self, path): (IN KB)                                        

    def file_unlink(self, filename): #DELETE

    def file_write(self, location, content, mode=None, owner=None, group=None, check=False,
                   strip=True, showout=True, append=False, sudo=False):

    def find(self, path, recursive=True, pattern="", findstatement="", type="", contentsearch="",
             executable=False, extendinfo=False):
        """

        @param findstatement can be used if you want to use your own find arguments
        for help on find see http://www.gnu.org/software/findutils/manual/html_mono/find.html

        @param pattern e.g. * / config / j*
            *   Matches any zero or more characters.
            ?   Matches any one character.
            [string] Matches exactly one character that is a member of the string string.

        @param type
            b    block(buffered) special
            c    character(unbuffered) special
            d    directory
            p    named pipe(FIFO)
            f    regular file
            l    symbolic link


        @param contentsearch
            looks for this content inside the files

        @param executable
            looks for executable files only

        @param extendinfo: this will return [[$path, $sizeinkb, $epochmod]]
        """

    def joinpaths(self, *args):

    def locale_check
    def locale_ensure

    def package_install(self, name):

    def pprint(self, text, lexer="bash"):
        """
        @format py3, bash
        """

    def replace(self, text, args={}):

    # -----------------------------------------------------------------------------

    def run(self, cmd, die=True, debug=None,  showout=True, profile=True, replace=True,
            shell=False, env=None, timeout=600, args={}):
        """
        return rc, out, err
        """    

    def touch(self, path):    

```                           

## properties

```python

class Tools():

    hostfile : setter/getter for the hostfile
    hostname

    platform_is_alpine
    platform_is_arch
    platform_is_cygwin
    platform_is_linux
    platform_is_osx
    platform_is_ubuntu

    networkinfo

    system_uuid
```
