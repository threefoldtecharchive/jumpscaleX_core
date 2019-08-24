# Builders guidlines

[Video with more explanation](https://drive.google.com/open?id=19uvro52lbOumFNPb7DrnORy31QKJKu6S)

## there are 3 directories used

- /sandbox      : sandbox directory, has the files in production 
- DIR_BUILD     : is the directory used for building e.g. compilation of a C program
    - build dir should only be relevant during build step and as starting point for install step 
    - property: self.DIR_BUILD
- DIR_SANDBOX  : the location from which we create an flist, files are copied in here from /sandbox (dont copy from /builddir)
  - property: self.DIR_SANDBOX

## methods / properties available in each builder class

### .reset()  

reset the state of your builder, important to let the state checking restart

### .tools:  Builder tools 
Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file
, write to a file, execute bash commands and many other handy methods that you will probably need in your builder)

[methods & properties of the tools lib](BuildersInternalToolsLib.md)

use them as much as you can !!!

they are under self.tools

### .system:  Some System Tools

see [Builders Internal System Lib](BuildersInternalSystemLib.md)

they are under self.system

### profile management

see [Builders Profile Management](BuildersProfileManagement.md)

### bash

Bash for the sandbox
e.g. self.bash.profile is very useful


## methods you should implement in your builder

### .build()

- builds from source code
- if possible build to separate directory, build to self.DIR_BUILD
- sometimes result is directly in sandbox (for certain components no choice e.g. openresty)
- is optional, maybe the installer uses already build packages e.g. on ubuntu 
- result: all components build which will be required by install

### .install()

- will automatically call build() at start
- copy relevant (only required) files to sandbox (bin/lib/...) from self.DIR_BUILD
- create config files if needed

### .test()

- a basic test to see if the build was successfull
- will automatically call start() at start
- will automatically call test_api() at end, is against localhost 
- is optional

### .test_api(ipaddr="localhost")

- will test the api on specified ipaddr e.g. rest calls, tcp calls, port checks, ...

### .test_zos(zhub_client,zos_client)

- a basic test to see if the build was successfull
- will automatically call sandbox(zhub_client=zhub_client) at start
- will start the container on specified zos_client with just build flist
- will call .test_api() with ip addr of the container


### .start()

- will automatically call install() at start
- start (for debug purposes) the server component (if it is a server component)
- is optional
- will use self.startup_cmds as basis 

### .stop()

- only for servers
- is optional
- will use self.startup_cmds as basis 

### .sandbox(zhub_client)

- copy all required files from /sandbox (NO OTHER LOCATION)  to self.DIR_SANDBOX
    - example: a binary loacted in `/sanbox/bin/{name}` should be copied to `{DIR_SANDBOX}/sandbox/bin/{name}`
    - directory structure as how it will be in flist and the container but chroot = `{DIR_SANDBOX}`
- this method will call: self._flist_create(zhub_client=zhub_client) which will create flist & upload to your zhub
- will return: the flist url 

### .clean()

- removes all files as result from building 

### .uninstall()

- optional, removes installed, build & sandboxed files

### .running()

- check that the daemon is running

### startup_cmds is a property

- get from j.tools.startupcmd
- is a way how to start any daemon in generic way, if you specify this one then start() stop() and running() do not need to be implemented



## methods which are on each builder to make life easy

### _replace(txt)

will replace arguments like {DIR_SANDBOX} but also arguments from  j.core.myenv.config inside the text

### ._write(path,txt)

- will write and also call self._replace()

### ._execute(txt)

- will write in {DIR_BUILD}/cmds/run.sh (which will replace)
- will run the {DIR_BUILD}/cmds/run.sh

### def _copy(src, dst):

- src & dest can be file, dir, ...

### def _remove(src):

- remove dir/file

## IMPORTANT INSTRUCTIONS HOW TO CREATE A BUILDER CLASS

- do not model metadata in e.g. _bins ...
    - no properties, no hidden models, ...
- maintain actor based paradigm where every method as described above is implemented using ONLY
    - self._replace, self._execute, ...  
    - self.tools...
    - j.builders....
    - j.sal...
    - j.tools...
    - self.system... 
- use the DSL in order as specified above first tools, then j.builder, then ...
- in each method you will not import python, use databases of any sort
- best practice: dont execute bash commands if primitive exists in self.tools or j...
