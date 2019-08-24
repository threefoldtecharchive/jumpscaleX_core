## Flist Generation (WRONG APPROACH DO NOT USE !!!!)

The BuilderBaseClass provides a functionality to create and upload flists.

For any builder you just need to set some attributes on the class of the builder and call builder.flist_create(zhub_instance_name), after building on the system first, and the tar will be created and uploaded to the hub using the zhub_instance name.

### The attributes:
- `bins`: list of binaries to copy to /sandbox/bin/ in the flist. The flist builder will also `ldd` the binaries and copy the relevant libs to /sandbox/lib/.
- `dirs`: a dict of files/dirs to copy from the host to the flist under /sandbox.
- `new_dirs`: a list of dirs to create under /sandbox/
- `new_files`: a dict of new files to create under /sandbox/, where the key is the location relative to /sandbox and the value is the content of the file.
- `startup`: contents of /.startup.toml file.
- `root_files`: a dict of new files to create under /, where the key is the location relative to / and the value is the content of the file.
- `root_dirs`: a dict of directories or files to be copied as is under /, where the key is the location and the value is the destination
