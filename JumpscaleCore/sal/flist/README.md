# Flist Manipulation 
### we using zflist binary in 0-flist repo
 
 to install it using kosmos
 ```
 j.builders.storage.zflist.install(reset=True)
 ```
 
## create new flist:
### create new flist then put file from local then commit it
```python
new_flist = j.sal.flist.new() 
new_flist.put("/sandbox/code/github/test.py","/") 
new_flist.commit("/sandbox/code/test.flist") 
#delete everything in temporary-point
new_flist.close()
```

## open flist and edit on it:
### open flist , put dir from local , commit it
```python
new_flist = j.sal.flist.open("/tmp/test.flist") 
new_flist.put_dir ("/tmp/test","/") 
# list all things in flist
new_flist.list_all()
new_flist.commit("/sandbox/code/test2.flist") 
#delete everything in temporary-point
new_flist.close()
```