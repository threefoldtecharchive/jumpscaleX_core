# BCDBFS
it's a virtual file system based on bcdb, every thing is stored in bcdb

# Usage example

## Creating files and directories
```python
j.sal.bcdbfs.dir_create("/test")
for i in range(5):
    j.sal.bcdbfs.dir_create("/test/dir_{}".format(i))
    j.sal.bcdbfs.file_create_empty("/test/test_{}".format(i))
    for k in range(5):
        j.sal.bcdbfs.file_create_empty(("/test/dir_{}/test_{}".format(i, k)))
```
## checking for existence and the entry type
```python
assert j.sal.bcdbfs.file_exists("/test/test_1")
assert j.sal.bcdbfs.dir_exists("/test/dir_1")
assert j.sal.bcdbfs.file_exists("/test/dir_1/test_4")

assert j.sal.bcdbfs.is_dir("/test/dir_1")
assert j.sal.bcdbfs.is_file("/test/dir_1/test_4")
```
## listing files and directories in a path
```python
assert j.sal.bcdbfs.list_files("/test/dir_1") == [
    "/test/dir_1/test_0",
    "/test/dir_1/test_1",
    "/test/dir_1/test_2",
    "/test/dir_1/test_3",
    "/test/dir_1/test_4",
]
assert j.sal.bcdbfs.list_dirs("/test") == ["/test/dir_0", "/test/dir_1", "/test/dir_2", "/test/dir_3", "/test/dir_4"]
assert j.sal.bcdbfs.list_files_and_dirs("/test") == [
    "/test/dir_0",
    "/test/dir_1",
    "/test/dir_2",
    "/test/dir_3",
    "/test/dir_4",
    "/test/test_0",
    "/test/test_1",
    "/test/test_2",
    "/test/test_3",
    "/test/test_4",
]
```
## Copying and deleting entries
```python
j.sal.bcdbfs.file_copy_form_bcdbfs("/test/test_0", "/test/test_copied")
j.sal.fs.createEmptyFile("/tmp/test_bcdbfs")
j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs", "/test/test_from_local")

assert j.sal.bcdbfs.file_exists("/test/test_from_local")

j.sal.bcdbfs.file_delete("/test/test_from_local")
assert j.sal.bcdbfs.file_exists("/test/test_from_local") is False
```

## Reading and writing files
```python
j.sal.fs.writeFile("/tmp/test_bcdbfs", "\ntest content\n\n\n")
j.sal.bcdbfs.file_copy_from_local("/tmp/test_bcdbfs", "/test/test_with_content")
assert j.sal.bcdbfs.file_read("/test/test_with_content") == b"\ntest content\n\n\n"
```

**Note:** To run the full snippet of the previous code run `j.sal.bcdbfs.test

## exists:
  
checks is the path exists, it can be a directory or a file  
:param path: the path to be checked  
:return: bool  
  

## is_dir:
  
checks if the path is a dir  
:param path: the path to checked  
:return: bool  
  

## is_file:
  
checks if the path is a file  
:param path: the path to checked  
:return: bool  
  

## dir_create:
  
create a directory  
:param path: full path of the directory  
:return: Directory object  
  

## dir_remove:
  
Remove directory  
:param path: directory path  
:param recursive: if true will perform recursive delete by deleting all sub directorie  
:return: None  
  

## dir_exists:
  
checks if path is an existing directory  
:param path: path to be checked  
:return: bool  
  

## dir_copy_from_local:
  
copy directory from local file system to bcdb  
:param path: full path of the directory (the directory must exist on the local file system)  
:param dest: dest to copy the dir to on bcdbfs  
:param recursive: copy subdirs  
:return:  
  

## dir_copy_from_bcdbfs:
  
copy directory from a location in bcdbfs file system to another  
:param path: full path of the directory (the directory must exist in bcdbfs)  
:param dest: dest to copy the dir to on bcdbfs  
:param recursive: copy subdirs  
:return:  
  

## dir_copy:
  
copies a dir from either local file system or from bcdbfs  
:param path: source path  
:param dest: destination  
:param recursive: copy subdirs  
:return:  
  

## file_create_empty:
  
Creates empty file  
:param filename: full file path  
:return: file object  
  

## file_write:
  
writes a file to bcdb  
:param path: the path to store the file  
:param content: content of the file to be written  
:param append: if True will append if the file already exists  
:param create: create new if true and the file doesn't exist  
:return: file object  
  

## file_copy_from_local:
  
copies file from local file system to bcdb  
:param path: path on local file system  
:param dest: destination on bcdbfs  
:return: file object  
  

## file_copy_form_bcdbfs:
  
copies file to another location in bcdbfs  
:param path: full path of the file  
:param dest: destination path  
:return: file object  
  

## file_copy:
  
copies file either from the local file system or from another location in bcdbfs  
:param path: full path to the file  
:param dest: destination path  
:return: file object  
  

## file_delete:
  
deletes a file  
:param path: a path of the file to be deleted  
:return: None  
  

## file_exists:
  
checks if the path is existing file  
:param path: path for a file to be checked  
:return: bool  
  

## file_read:
  
reads a file  
:param path: the path to the file to read  
:return: Bytes stream  
  

## list_dirs:
  
list dirs in path  
:param path: path to an existing directory  
:return: List[str] full paths  
  

## list_files:
  
list files in path  
:param path: path to an existing directory  
:return: List[str] full paths  
  

## list_files_and_dirs:
  
list files and dirs in path  
:param path: path to an existing directory  
:return: List[str] full paths  
  

## search:
  
search in the content of files in a specific loaction  
:param text: text to search for  
:param location: location to search in, default: /  
:return: List[str] full paths  

