# logdict format

```python
logdict["filepath"] = fname     #path of the file where the log came from    
logdict["linenr"] = linenr  
logdict["processid"] =          #the process id if known
logdict["message"] = msg        
logdict["public"] = msg         #optional public message
logdict["level"] = level        #10-50
logdict["context"] =            #e.g. name of a definition or class
logdict["cat"] =                #a freely chosen category can be in dot notation e.g. performance.cpu.high
logdict["data"] =               #data can be attached to a log e.g. a data object
tbline = 
logdict["traceback"] = [tbline1,tbline2]        #list of traceback elements

```


## log (error) levels

- CRITICAL 	50
- ERROR 	40
- WARNING 	30
- INFO 	    20
- STDOUT 	15
- DEBUG 	10



